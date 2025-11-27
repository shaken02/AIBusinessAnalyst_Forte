"""Движок для анализа кода через LLM."""

import json
from typing import Any, Dict, List, Optional

from code_review_backend.config import config
from code_review_backend.prompts import format_review_prompt

# Используем Gemini напрямую
def create_engine(model_name: Optional[str] = None):
    """Создает Gemini engine напрямую."""
    import google.generativeai as genai
    
    genai.configure(api_key=config.gemini.api_key)
    model_name_to_use = model_name or config.gemini.model_name
    model = genai.GenerativeModel(model_name_to_use)
    
    class DirectGeminiEngine:
        def __init__(self):
            self.model = model
            self.generation_config = {
                "temperature": config.gemini.temperature,
                "top_p": 0.9,
                "max_output_tokens": config.gemini.max_output_tokens,
            }
        
        def ask(self, prompt: str) -> str:
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(**self.generation_config)
                )
                try:
                    return response.text.strip()
                except (ValueError, AttributeError):
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            parts_text = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    parts_text.append(part.text)
                            if parts_text:
                                return ' '.join(parts_text).strip()
                    return ""
            except Exception as e:
                print(f"[ERROR] Gemini API error: {e}")
                raise
    
    return DirectGeminiEngine()


class ReviewResult:
    """Результат анализа кода."""
    
    def __init__(self, raw_response: str):
        self.raw_response = raw_response
        self.parsed: Optional[Dict[str, Any]] = None
        self._parse_response()
    
    def _parse_response(self):
        """Парсит JSON ответ от LLM."""
        try:
            response_text = self.raw_response.strip()
            
            # Если ответ начинается с ```json или ```, извлекаем JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            
            self.parsed = json.loads(response_text)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Failed to parse JSON response: {e}")
            # Попытка извлечь JSON вручную
            try:
                start_idx = self.raw_response.find("{")
                end_idx = self.raw_response.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = self.raw_response[start_idx:end_idx + 1]
                    self.parsed = json.loads(json_str)
                    return
            except Exception as e2:
                print(f"[ERROR] Manual extraction also failed: {e2}")
            
            self.parsed = {
                "files": [],
                "error": "Не удалось распарсить ответ от AI"
            }
    
    @property
    def verdict(self) -> str:
        """Вердикт: APPROVE, CHANGES_REQUESTED, REJECT"""
        return self.parsed.get("verdict", "CHANGES_REQUESTED")
    
    @property
    def summary(self) -> str:
        """Краткое резюме анализа."""
        return self.parsed.get("summary", "")
    
    @property
    def verdict_explanation(self) -> str:
        """Объяснение вердикта."""
        return self.parsed.get("verdict_explanation", "")
    
    @property
    def critical_issues(self) -> List[Dict[str, Any]]:
        """Список критических проблем."""
        return self.parsed.get("critical_issues", [])
    
    @property
    def suggestions(self) -> List[str]:
        """Рекомендации."""
        return self.parsed.get("suggestions", [])
    
    @property
    def files(self) -> List[Dict[str, Any]]:
        """Список результатов анализа по файлам."""
        return self.parsed.get("files", [])


class ReviewEngine:
    """Движок для анализа кода через LLM."""
    
    def __init__(self):
        print("[INFO] Initializing ReviewEngine with Gemini...")
        try:
            self.llm = create_engine(config.gemini.model_name)
            print(f"[INFO] ReviewEngine initialized successfully with model: {config.gemini.model_name}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize ReviewEngine: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def review_mr(
        self,
        mr_title: str,
        mr_description: str,
        author_name: str,
        target_branch: str,
        source_branch: str,
        all_diffs: str
    ) -> ReviewResult:
        """
        Анализирует все файлы Merge Request одним запросом через LLM.
        
        Args:
            mr_title: Название MR
            mr_description: Описание MR
            author_name: Имя автора
            target_branch: Целевая ветка
            source_branch: Исходная ветка
            all_diffs: Diff всех измененных файлов
        
        Returns:
            ReviewResult с результатами анализа
        """
        # Формируем промпт
        prompt = format_review_prompt(
            mr_title=mr_title,
            mr_description=mr_description,
            author_name=author_name,
            target_branch=target_branch,
            source_branch=source_branch,
            all_diffs=all_diffs
        )
        
        # Отправляем в LLM
        print(f"[INFO] Sending request to Gemini API for all files...")
        response = self.llm.ask(prompt)
        print(f"[INFO] Received response from Gemini (length: {len(response)} chars)")
        
        # Логируем начало ответа для отладки
        response_preview = response[:200].replace("\n", "\\n")
        print(f"[DEBUG] Response preview: {response_preview}...")
        
        # Парсим результат
        print(f"[INFO] Parsing Gemini response...")
        result = ReviewResult(response)
        
        # Проверяем, успешно ли распарсилось
        if "error" in result.parsed:
            print(f"[WARNING] Failed to parse response! Full response saved for debugging.")
            print(f"[DEBUG] Full response:\n{response}")
        else:
            files_count = len(result.files)
            print(f"[INFO] ✓ Response parsed successfully, analyzed {files_count} file(s)")
        
        return result
    
    def format_review_comment(self, result: ReviewResult) -> str:
        """Форматирует результаты анализа всех файлов в один комментарий."""
        lines = []
        
        files_data = result.files
        if not files_data:
            if "error" in result.parsed:
                lines.append("## ❌ AI Code Review: ОШИБКА")
                lines.append("")
                lines.append(f"**Ошибка:** {result.parsed.get('error', 'Неизвестная ошибка')}")
                return "\n".join(lines)
            else:
                lines.append("## ⚠️ AI Code Review: НЕТ ДАННЫХ")
                return "\n".join(lines)
        
        # Подсчитываем общий вердикт
        verdicts = [f.get("verdict", "CHANGES_REQUESTED") for f in files_data]
        if all(v == "APPROVE" for v in verdicts):
            overall_verdict = "APPROVE"
            overall_emoji = "✅"
        elif any(v == "REJECT" for v in verdicts):
            overall_verdict = "REJECT"
            overall_emoji = "❌"
        else:
            overall_verdict = "CHANGES_REQUESTED"
            overall_emoji = "❓"
        
        lines.append(f"## {overall_emoji} AI Code Review: {overall_verdict}")
        lines.append("")
        lines.append(f"Проанализировано файлов: {len(files_data)}")
        lines.append("")
        
        # Результаты по каждому файлу
        for file_data in files_data:
            file_path = file_data.get("file_path", "unknown")
            verdict = file_data.get("verdict", "CHANGES_REQUESTED")
            what_changed = file_data.get("what_changed", "")
            verdict_explanation = file_data.get("verdict_explanation", "")
            critical_issues = file_data.get("critical_issues", [])
            suggestions = file_data.get("suggestions", [])
            
            # Вердикт для файла
            verdict_emoji = ""
            if verdict == "APPROVE":
                verdict_emoji = "✅"
            elif verdict == "CHANGES_REQUESTED":
                verdict_emoji = "❓"
            elif verdict == "REJECT":
                verdict_emoji = "❌"
            
            lines.append(f"### {verdict_emoji} Файл: `{file_path}` - {verdict}")
            lines.append("")
            
            # Что пытались изменить
            if what_changed:
                lines.append(f"**Что изменено:** {what_changed}")
                lines.append("")
            
            # Объяснение вердикта
            if verdict_explanation:
                lines.append(f"**Почему такое решение:** {verdict_explanation}")
                lines.append("")
            
            # Проблемы
            if critical_issues:
                lines.append("**Найденные проблемы:**")
                for idx, issue in enumerate(critical_issues[:5], 1):
                    line = issue.get("line", "?")
                    issue_type = issue.get("type", "error")
                    message = issue.get("message", "")
                    why = issue.get("why", "")
                    fix = issue.get("fix", "")
                    
                    lines.append(f"{idx}. Строка {line} ({issue_type})")
                    if message:
                        lines.append(f"   - Что не так: {message}")
                    if why:
                        lines.append(f"   - Почему это проблема: {why}")
                    if fix:
                        lines.append(f"   - Как исправить: {fix}")
                    lines.append("")
            
            # Рекомендации
            if suggestions:
                lines.append("**Рекомендации:**")
                for suggestion in suggestions[:3]:
                    lines.append(f"- {suggestion}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
