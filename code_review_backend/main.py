"""FastAPI приложение для AI Code Review через GitLab webhooks."""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Добавляем родительскую директорию в PYTHONPATH для импортов
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
import uvicorn

from code_review_backend.config import config
from code_review_backend.gitlab_client import GitLabClient
from code_review_backend.review_engine import ReviewEngine
from code_review_backend.webhook_handler import extract_mr_data, extract_push_data, verify_webhook_signature

app = FastAPI(
    title="AI Code Review Assistant",
    description="Автоматический code review через GitLab webhooks и Gemini AI",
    version="1.0.0"
)

# Инициализация компонентов
gitlab_client = GitLabClient()
review_engine = ReviewEngine()

# Кэш для отслеживания уже обработанных MR (защита от дубликатов)
processed_mr_cache: Dict[str, str] = {}  # {mr_key: last_comment_hash}
diff_hash_cache: Dict[str, str] = {}  # {mr_key: last_diff_hash} - для проверки изменений diff
diff_cache: Dict[str, Dict[str, Any]] = {}  # {mr_key: {"hash": ..., "diff": ..., "timestamp": ...}} - кэш самого diff
push_review_cache: Dict[str, Dict[str, Any]] = {}  # {f"{project_id}:{branch}": {"review_result": ..., "comment": ..., "diff_hash": ...}}


@app.get("/")
async def root():
    """Корневой endpoint для проверки работы сервера."""
    return {
        "status": "ok",
        "service": "AI Code Review Assistant",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def _get_mr_cache_key(project_id: str, mr_iid: int) -> str:
    """Генерирует ключ для кэша MR."""
    return f"{project_id}:{mr_iid}"


def _get_comment_hash(comment: str) -> str:
    """Генерирует хеш комментария для проверки дубликатов."""
    import hashlib
    return hashlib.md5(comment.encode()).hexdigest()[:8]


def _has_recent_ai_comment(project_id: str, mr_iid: int, comment_hash: str) -> bool:
    """
    Проверяет, был ли уже опубликован такой же комментарий от AI недавно.
    
    Returns:
        True если комментарий уже был опубликован
    """
    cache_key = _get_mr_cache_key(project_id, mr_iid)
    cached_hash = processed_mr_cache.get(cache_key)
    
    if cached_hash == comment_hash:
        return True
    
    # Проверяем в GitLab - есть ли комментарий от AI
    try:
        notes = gitlab_client.get_mr_notes(project_id, mr_iid)
        # Ищем комментарии содержащие "AI Code Review"
        for note in notes[-5:]:  # Проверяем последние 5 комментариев
            body = note.get("body", "")
            if "AI Code Review" in body:
                # Проверяем хеш комментария
                note_hash = _get_comment_hash(body)
                if note_hash == comment_hash:
                    processed_mr_cache[cache_key] = comment_hash
                    return True
    except Exception as e:
        print(f"[WARNING] Failed to check existing comments: {e}")
    
    return False


@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str = Header(None, alias="X-Gitlab-Token")
):
    """
    Обрабатывает webhook события от GitLab.
    
    Ожидает события типа 'merge_request' и автоматически анализирует код.
    """
    print(f"[WEBHOOK] Received request from {request.client.host}")
    try:
        body = await request.body()
        
        # Проверяем подпись
        if not verify_webhook_signature(body, x_gitlab_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Парсим JSON
        payload: Dict[str, Any] = await request.json()
        object_kind = payload.get("object_kind")
        print(f"[WEBHOOK] Received {object_kind} event from {request.client.host}")
        
        # ИГНОРИРУЕМ комментарии (note) - они не требуют обработки
        if object_kind == "note":
            print(f"[INFO] Ignoring note event (comment posted)")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Note event ignored"}
            )
        
        # Извлекаем данные о MR или Push
        mr_data = extract_mr_data(payload)
        push_data = extract_push_data(payload)
        
        if mr_data:
            # Это MR событие
            state = mr_data.get("state", "")
            if state in ["closed", "merged"]:
                print(f"[INFO] Skipping MR #{mr_data.get('mr_iid')} - state is '{state}'")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"message": f"MR state is '{state}', ignoring"}
                )
            
            action = mr_data.get("action")
            print(f"[WEBHOOK] MR action: '{action}'")
            
            # ИГНОРИРУЕМ action 'approved' - это мы сами одобрили, не нужно обрабатывать снова
            if action == "approved":
                print(f"[INFO] Skipping MR action 'approved' (we approved it ourselves)")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"message": "Approved action ignored"}
                )
            
            if action not in ["open", "update", "reopen"]:
                print(f"[INFO] Skipping MR action '{action}' (only processing: open, update, reopen)")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"message": f"Action '{action}' not processed"}
                )
            
            # Запускаем анализ в фоне
            asyncio.create_task(process_mr_review(mr_data))
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Webhook received, processing MR review",
                    "mr_iid": mr_data.get("mr_iid"),
                    "project_id": mr_data.get("project_id")
                }
            )
        
        elif push_data:
            # Это Push событие
            print(f"[WEBHOOK] Push event for branch: {push_data.get('branch')}")
            asyncio.create_task(process_push_review(push_data))
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Webhook received, processing push review",
                    "branch": push_data.get("branch")
                }
            )
        
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Not a merge request or push event, ignoring"}
            )
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Webhook processing failed: {e}")
        print(f"[ERROR] Traceback:\n{error_trace}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


async def process_mr_review(mr_data: Dict[str, Any]):
    """Обрабатывает анализ Merge Request."""
    try:
        project_id = str(mr_data["project_id"])
        mr_iid = mr_data["mr_iid"]
        cache_key = _get_mr_cache_key(project_id, mr_iid)
        source_branch = mr_data.get("source_branch", "")
        action = mr_data.get("action", "")
        
        print(f"[INFO] ===== STARTING MR REVIEW #{mr_iid} =====")
        print(f"[INFO] Project: {project_id}, MR IID: {mr_iid}")
        print(f"[INFO] Title: {mr_data.get('mr_title', 'N/A')[:50]}...")
        
        # ОПТИМИЗАЦИЯ: Сначала проверяем кэш diff - если есть, используем его вместо запроса к GitLab
        import hashlib
        cached_diff_data = diff_cache.get(cache_key)
        diff = None
        current_diff_hash = None
        
        if cached_diff_data:
            cached_diff_hash = cached_diff_data.get("hash")
            cached_diff = cached_diff_data.get("diff")
            print(f"[INFO] Found cached diff data (hash: {cached_diff_hash})")
            
            # Вычисляем хеш из кэшированного diff для проверки
            diff_content_for_hash = []
            for file_change in cached_diff:
                file_diff_content = file_change.get("diff", "")
                if file_diff_content and file_diff_content.strip():
                    diff_content_for_hash.append(file_diff_content)
            
            if diff_content_for_hash:
                diff_hash_string = "\n".join(diff_content_for_hash)
                computed_hash = hashlib.md5(diff_hash_string.encode()).hexdigest()[:8]
                
                if computed_hash == cached_diff_hash:
                    print(f"[INFO] Using cached diff (hash matches: {cached_diff_hash})")
                    diff = cached_diff
                    current_diff_hash = cached_diff_hash
                else:
                    print(f"[INFO] Cached diff hash mismatch, will fetch new diff")
        
        # Если diff не в кэше или хеш не совпадает - получаем из GitLab
        if diff is None:
            print(f"[INFO] [1/5] Fetching MR changes (diff) from GitLab...")
            mr_changes = gitlab_client.get_mr_changes(project_id, mr_iid)
            diff = mr_changes.get("changes", [])
            
            if not diff:
                print(f"[WARNING] No file changes to analyze, skipping review")
                return
            
            # Вычисляем хеш нового diff
            diff_content_for_hash = []
            for file_change in diff:
                file_diff_content = file_change.get("diff", "")
                if file_diff_content and file_diff_content.strip():
                    diff_content_for_hash.append(file_diff_content)
            
            if not diff_content_for_hash:
                print(f"[WARNING] No file changes to analyze, skipping review")
                return
            
            # Вычисляем хеш только из содержимого diff (без форматирования)
            diff_hash_string = "\n".join(diff_content_for_hash)
            current_diff_hash = hashlib.md5(diff_hash_string.encode()).hexdigest()[:8]
            print(f"[INFO] Computed diff hash: {current_diff_hash}")
            
            # Сохраняем diff в кэш
            diff_cache[cache_key] = {
                "hash": current_diff_hash,
                "diff": diff,
                "timestamp": time.time()
            }
            print(f"[INFO] Saved diff to cache")
        
        # Проверяем, не обрабатывали ли мы уже этот diff
        cached_diff_hash = diff_hash_cache.get(cache_key)
        if cached_diff_hash:
            print(f"[INFO] Found cached diff hash: {cached_diff_hash}")
            if cached_diff_hash == current_diff_hash:
                print(f"[INFO] Diff unchanged (hash: {current_diff_hash}), skipping review")
                print(f"[INFO] ===== SKIPPED MR REVIEW #{mr_iid} (no changes) =====")
                return
            else:
                print(f"[INFO] Diff changed (cached: {cached_diff_hash}, current: {current_diff_hash}), will analyze")
        else:
            print(f"[INFO] No cached diff hash found, will analyze")
        
        # Получаем информацию о MR (только если diff изменился)
        print(f"[INFO] [2/5] Fetching MR info from GitLab...")
        mr_info = gitlab_client.get_mr_info(project_id, mr_iid)
        
        # Форматируем diff для дальнейшей обработки
        all_diffs_text_for_hash = []
        for file_change in diff:
            file_path = file_change.get("new_path", file_change.get("old_path", "unknown"))
            file_diff_content = file_change.get("diff", "")
            if file_diff_content and file_diff_content.strip():
                all_diffs_text_for_hash.append(f"=== Файл: {file_path} ===")
                all_diffs_text_for_hash.append(file_diff_content)
                all_diffs_text_for_hash.append("")
        
        all_diffs_combined_for_hash = "\n".join(all_diffs_text_for_hash)
        
        # Проверяем, есть ли сохраненный анализ от push для этой ветки
        push_cache_key = f"{project_id}:{source_branch}"
        if action == "open" and push_cache_key in push_review_cache:
            print(f"[INFO] Found cached push review for branch '{source_branch}', using it...")
            cached_review = push_review_cache[push_cache_key]
            cached_diff_hash = cached_review.get("diff_hash")
            
            # Проверяем, что diff совпадает (используем уже вычисленный хеш)
            print(f"[INFO] Comparing diff hashes - cached: {cached_diff_hash}, current: {current_diff_hash}")
            if cached_diff_hash == current_diff_hash:
                print(f"[INFO] Using cached review (diff hash matches: {current_diff_hash})")
                # Используем сохраненный результат
                review_result = cached_review["review_result"]
                comment = cached_review["comment"]
                comment_hash = cached_review["comment_hash"]
                
                # Пропускаем анализ через LLM, сразу публикуем
                print(f"[INFO] [3/5] Skipping Gemini analysis (using cached result)")
                
                # Определяем общий вердикт
                files_data = review_result.files
                if files_data:
                    verdicts = [f.get("verdict", "CHANGES_REQUESTED") for f in files_data]
                    if all(v == "APPROVE" for v in verdicts):
                        overall_verdict = "APPROVE"
                    elif any(v == "REJECT" for v in verdicts):
                        overall_verdict = "REJECT"
                    else:
                        overall_verdict = "CHANGES_REQUESTED"
                else:
                    overall_verdict = "CHANGES_REQUESTED"
                
                print(f"[INFO] Overall verdict: {overall_verdict} (from cached review)")
                
                # ЗАЩИТА ОТ ДУБЛИКАТОВ: проверяем был ли уже такой комментарий
                if _has_recent_ai_comment(project_id, mr_iid, comment_hash):
                    print(f"[INFO] Skipping duplicate comment for MR #{mr_iid} (same comment already exists)")
                    print(f"[INFO] ===== SKIPPED MR REVIEW #{mr_iid} (duplicate) =====")
                    # Удаляем из push кэша, так как уже использовали
                    if push_cache_key in push_review_cache:
                        del push_review_cache[push_cache_key]
                    return
                
                # Публикуем комментарий
                print(f"[INFO] [4/5] Posting cached comment to GitLab MR #{mr_iid}...")
                gitlab_client.post_mr_comment(project_id=project_id, mr_iid=mr_iid, body=comment)
                print(f"[INFO] [4/5] ✓ Comment posted successfully")
                
                # Обновляем лейблы
                print(f"[INFO] [5/5] Updating MR labels and merge status...")
                labels = []
                if overall_verdict == "APPROVE":
                    labels = ["ai-reviewed", "ready-for-merge"]
                    try:
                        gitlab_client.unblock_merge(project_id, mr_iid)
                        gitlab_client.approve_mr(project_id, mr_iid)
                        print(f"[INFO] [5/5] ✓ MR #{mr_iid} approved and merge unblocked")
                    except Exception as e:
                        print(f"[WARNING] Failed to approve/unblock MR: {e}")
                elif overall_verdict == "CHANGES_REQUESTED":
                    labels = ["ai-reviewed", "changes-requested"]
                    try:
                        gitlab_client.block_merge(project_id, mr_iid)
                        print(f"[INFO] [5/5] ✓ MR #{mr_iid} merge blocked - changes requested")
                    except Exception as e:
                        print(f"[WARNING] Failed to block MR: {e}")
                elif overall_verdict == "REJECT":
                    labels = ["ai-reviewed", "rejected"]
                    try:
                        gitlab_client.block_merge(project_id, mr_iid)
                        print(f"[INFO] [5/5] ✓ MR #{mr_iid} merge blocked - rejected")
                    except Exception as e:
                        print(f"[WARNING] Failed to block MR: {e}")
                
                if labels:
                    current_labels = mr_info.get("labels", [])
                    all_labels = list(set(current_labels + labels))
                    gitlab_client.update_mr_labels(project_id, mr_iid, all_labels)
                    print(f"[INFO] [5/5] ✓ Labels updated: {', '.join(labels)}")
                
                # Сохраняем в кэш
                processed_mr_cache[cache_key] = comment_hash
                diff_hash_cache[cache_key] = current_diff_hash
                
                # Удаляем из push кэша, так как уже использовали
                del push_review_cache[push_cache_key]
                
                print(f"[INFO] ===== COMPLETED MR REVIEW #{mr_iid} (from cache) =====")
                print(f"[INFO] ✓ Анализ завершен (использован кэш от push)")
                print(f"[INFO] ✓ Комментарий опубликован в GitLab")
                print(f"[INFO] ✓ Лейблы обновлены")
                print(f"[INFO] ✓ Статус merge: {'разблокирован' if overall_verdict == 'APPROVE' else 'заблокирован'}")
                print(f"[INFO] ========================================")
                print(f"[INFO] Готов к следующему запросу. Ожидание...")
                print(f"[INFO] ========================================")
                return
            else:
                print(f"[INFO] Cached review diff hash mismatch, will do fresh analysis")
        
        # Подсчитываем файлы
        num_files = len(diff)
        print(f"[INFO] Found {num_files} file(s) changed in MR #{mr_iid}")
        if num_files > 0:
            file_names = [ch.get("new_path", ch.get("old_path", "unknown")) for ch in diff[:5]]
            print(f"[INFO] Files: {', '.join(file_names)}{' ...' if num_files > 5 else ''}")
        
        # Форматируем все diff'ы в один текст
        all_diffs_text = []
        for file_change in diff:
            file_path = file_change.get("new_path", file_change.get("old_path", "unknown"))
            file_diff_content = file_change.get("diff", "")
            
            if not file_diff_content or file_diff_content.strip() == "":
                continue
            
            all_diffs_text.append(f"=== Файл: {file_path} ===")
            all_diffs_text.append(file_diff_content)
            all_diffs_text.append("")
        
        if not all_diffs_text:
            print(f"[WARNING] No file changes to analyze, skipping review")
            return
        
        all_diffs_combined = "\n".join(all_diffs_text)
        
        # Хеш уже проверен выше, продолжаем анализ
        print(f"[INFO] Diff hash: {current_diff_hash} (will process)")
        
        # Анализируем все файлы одним запросом через LLM
        print(f"[INFO] [3/5] Analyzing {num_files} file(s) in one request...")
        review_result = review_engine.review_mr(
            mr_title=mr_data["mr_title"],
            mr_description=mr_data["mr_description"],
            author_name=mr_data["author_name"],
            target_branch=mr_data["target_branch"],
            source_branch=mr_data["source_branch"],
            all_diffs=all_diffs_combined
        )
        
        # Определяем общий вердикт на основе результатов по файлам
        files_data = review_result.files
        if not files_data:
            print(f"[WARNING] No files analyzed, skipping review")
            return
        
        verdicts = [f.get("verdict", "CHANGES_REQUESTED") for f in files_data]
        if all(v == "APPROVE" for v in verdicts):
            overall_verdict = "APPROVE"
        elif any(v == "REJECT" for v in verdicts):
            overall_verdict = "REJECT"
        else:
            overall_verdict = "CHANGES_REQUESTED"
        
        print(f"[INFO] [3/5] ✓ Gemini analysis completed")
        print(f"[INFO] Overall verdict: {overall_verdict} (based on {len(files_data)} file(s))")
        
        # Форматируем комментарий
        print(f"[INFO] [4/5] Formatting review comment...")
        comment = review_engine.format_review_comment(review_result)
        comment_hash = _get_comment_hash(comment)
        
        # ЗАЩИТА ОТ ДУБЛИКАТОВ: проверяем был ли уже такой комментарий
        if _has_recent_ai_comment(project_id, mr_iid, comment_hash):
            print(f"[INFO] Skipping duplicate comment for MR #{mr_iid} (same comment already exists)")
            print(f"[INFO] ===== SKIPPED MR REVIEW #{mr_iid} (duplicate) =====")
            return
        
        # Сохраняем в кэш (ПЕРЕД публикацией, чтобы избежать дубликатов)
        cache_key = _get_mr_cache_key(project_id, mr_iid)
        processed_mr_cache[cache_key] = comment_hash
        diff_hash_cache[cache_key] = current_diff_hash  # Сохраняем diff_hash после анализа
        
        # Обновляем кэш diff (если еще не сохранен)
        if cache_key not in diff_cache or diff_cache[cache_key].get("hash") != current_diff_hash:
            diff_cache[cache_key] = {
                "hash": current_diff_hash,
                "diff": diff,
                "timestamp": time.time()
            }
        
        print(f"[INFO] Saved diff hash to cache: {current_diff_hash} for MR #{mr_iid}")
        
        # Отправляем комментарий в GitLab
        print(f"[INFO] [4/5] Posting comment to GitLab MR #{mr_iid}...")
        gitlab_client.post_mr_comment(
            project_id=project_id,
            mr_iid=mr_iid,
            body=comment
        )
        print(f"[INFO] [4/5] ✓ Comment posted successfully")
        
        # Обновляем лейблы и блокируем/разблокируем merge
        print(f"[INFO] [5/5] Updating MR labels and merge status...")
        labels = []
        if overall_verdict == "APPROVE":
            labels = ["ai-reviewed", "ready-for-merge"]
            try:
                gitlab_client.unblock_merge(project_id, mr_iid)
                gitlab_client.approve_mr(project_id, mr_iid)
                print(f"[INFO] [5/5] ✓ MR #{mr_iid} approved and merge unblocked")
            except Exception as e:
                print(f"[WARNING] Failed to approve/unblock MR: {e}")
        elif overall_verdict == "CHANGES_REQUESTED":
            labels = ["ai-reviewed", "changes-requested"]
            try:
                gitlab_client.block_merge(project_id, mr_iid)
                print(f"[INFO] [5/5] ✓ MR #{mr_iid} merge blocked - changes requested")
            except Exception as e:
                print(f"[WARNING] Failed to block MR: {e}")
        elif overall_verdict == "REJECT":
            labels = ["ai-reviewed", "rejected"]
            try:
                gitlab_client.block_merge(project_id, mr_iid)
                print(f"[INFO] [5/5] ✓ MR #{mr_iid} merge blocked - rejected")
            except Exception as e:
                print(f"[WARNING] Failed to block MR: {e}")
        
        if labels:
            current_labels = mr_info.get("labels", [])
            all_labels = list(set(current_labels + labels))
            gitlab_client.update_mr_labels(project_id, mr_iid, all_labels)
            print(f"[INFO] [5/5] ✓ Labels updated: {', '.join(labels)}")
        
        print(f"[INFO] ===== COMPLETED MR REVIEW #{mr_iid} =====")
        print(f"[INFO] ✓ Анализ завершен успешно")
        print(f"[INFO] ✓ Комментарий опубликован в GitLab")
        print(f"[INFO] ✓ Лейблы обновлены")
        print(f"[INFO] ✓ Статус merge: {'разблокирован' if overall_verdict == 'APPROVE' else 'заблокирован'}")
        print(f"[INFO] ========================================")
        print(f"[INFO] Готов к следующему запросу. Ожидание...")
        print(f"[INFO] ========================================")
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Failed to process MR review: {e}")
        print(f"[ERROR] Full traceback:\n{error_trace}")


async def process_push_review(push_data: Dict[str, Any]):
    """Обрабатывает анализ кода при push событии."""
    try:
        project_id = str(push_data["project_id"])
        branch = push_data["branch"]
        commits = push_data["commits"]
        
        print(f"[INFO] Processing push review: project={project_id}, branch={branch}, commits={len(commits)}")
        
        if not commits:
            return
        
        last_commit_sha = commits[-1].get("id")
        if not last_commit_sha:
            return
        
        # Получаем diff
        try:
            compare_result = gitlab_client.compare_branches(project_id, "main", branch)
            diffs = compare_result.get("diffs", [])
        except Exception as e:
            print(f"[WARNING] Failed to get diff: {e}")
            return
        
        if not diffs:
            print(f"[WARNING] No diffs found in push event")
            return
        
        # Форматируем diff для анализа (как в process_mr_review)
        all_diffs_text = []
        diff_content_for_hash = []  # Для вычисления хеша - только содержимое diff
        for file_change in diffs:
            file_path = file_change.get("new_path", file_change.get("old_path", "unknown"))
            file_diff_content = file_change.get("diff", "")
            if file_diff_content and file_diff_content.strip():
                # Для форматирования (для анализа)
                all_diffs_text.append(f"=== Файл: {file_path} ===")
                all_diffs_text.append(file_diff_content)
                all_diffs_text.append("")
                # Для хеша (только содержимое diff, без форматирования)
                diff_content_for_hash.append(file_diff_content)
        
        all_diffs_combined = "\n".join(all_diffs_text)
        
        # Вычисляем хеш diff ТОЛЬКО из содержимого diff (без форматирования) - как в process_mr_review
        import hashlib
        if diff_content_for_hash:
            diff_hash_string = "\n".join(diff_content_for_hash)
            diff_hash = hashlib.md5(diff_hash_string.encode()).hexdigest()[:8]
            print(f"[INFO] Computed push diff hash: {diff_hash}")
        else:
            print(f"[WARNING] No diff content for hash calculation")
            return
        
        # Анализируем через LLM
        print(f"[INFO] Analyzing push changes for branch '{branch}'...")
        review_result = review_engine.review_mr(
            mr_title=f"Push to {branch}",
            mr_description=f"Автоматический анализ push в ветку {branch}",
            author_name=push_data["author_name"],
            target_branch="main",
            source_branch=branch,
            all_diffs=all_diffs_combined
        )
        
        # Форматируем комментарий
        comment = review_engine.format_review_comment(review_result)
        comment_hash = _get_comment_hash(comment)
        
        print(f"[INFO] Push review completed. Verdict: {review_result.verdict if hasattr(review_result, 'verdict') else 'N/A'}")
        
        # Ищем существующий MR для этой ветки
        try:
            mrs = gitlab_client.get_open_mrs_for_branch(project_id, branch)
            if mrs:
                mr = mrs[0]
                mr_iid = mr.get("iid")
                
                # Проверяем дубликаты
                if not _has_recent_ai_comment(project_id, mr_iid, comment_hash):
                    gitlab_client.post_mr_comment(project_id, mr_iid, body=comment)
                    
                    # Блокируем/разблокируем merge
                    files_data = review_result.files
                    if files_data:
                        verdicts = [f.get("verdict", "CHANGES_REQUESTED") for f in files_data]
                        if all(v == "APPROVE" for v in verdicts):
                            overall_verdict = "APPROVE"
                        elif any(v == "REJECT" for v in verdicts):
                            overall_verdict = "REJECT"
                        else:
                            overall_verdict = "CHANGES_REQUESTED"
                    else:
                        overall_verdict = "CHANGES_REQUESTED"
                    
                    if overall_verdict == "APPROVE":
                        gitlab_client.unblock_merge(project_id, mr_iid)
                        gitlab_client.approve_mr(project_id, mr_iid)
                    elif overall_verdict in ["CHANGES_REQUESTED", "REJECT"]:
                        gitlab_client.block_merge(project_id, mr_iid)
                    
                    print(f"[INFO] ✓ Push review posted to MR #{mr_iid}")
                    print(f"[INFO] ===== PUSH REVIEW COMPLETED =====")
                    print(f"[INFO] ✓ Анализ завершен")
                    print(f"[INFO] ✓ Комментарий опубликован в MR #{mr_iid}")
                    print(f"[INFO] ========================================")
            else:
                # MR еще не создан - сохраняем результат в кэш
                push_cache_key = f"{project_id}:{branch}"
                push_review_cache[push_cache_key] = {
                    "review_result": review_result,
                    "comment": comment,
                    "comment_hash": comment_hash,
                    "diff_hash": diff_hash,
                    "timestamp": time.time()
                }
                print(f"[INFO] ===== PUSH REVIEW COMPLETED =====")
                print(f"[INFO] ✓ Анализ завершен")
                print(f"[INFO] ✓ Результат сохранен в кэш для будущего MR")
                print(f"[INFO] ✓ Когда MR будет создан, комментарий опубликуется автоматически")
                print(f"[INFO] ========================================")
        except Exception as e:
            print(f"[WARNING] Failed to find/post to MR: {e}")
            # Все равно сохраняем в кэш на случай если MR создадут позже
            push_cache_key = f"{project_id}:{branch}"
            push_review_cache[push_cache_key] = {
                "review_result": review_result,
                "comment": comment,
                "comment_hash": comment_hash,
                "diff_hash": diff_hash,
                "timestamp": time.time()
            }
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Failed to process push review: {e}")
        print(f"[ERROR] Full traceback:\n{error_trace}")


def format_diff(changes: list) -> str:
    """Форматирует diff для анализа."""
    if not changes:
        return "Нет изменений"
    
    diff_lines = []
    for change in changes:
        old_path = change.get("old_path", "")
        new_path = change.get("new_path", "")
        diff_content = change.get("diff", "")
        
        if old_path != new_path:
            diff_lines.append(f"File renamed: {old_path} → {new_path}")
        else:
            diff_lines.append(f"File: {new_path}")
        
        diff_lines.append(diff_content)
        diff_lines.append("")
    
    return "\n".join(diff_lines)


if __name__ == "__main__":
    uvicorn.run(
        "code_review_backend.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )
