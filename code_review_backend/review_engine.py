"""Движок для анализа кода через LLM."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from code_review_backend.config import config
from code_review_backend.prompts import format_review_prompt

# Добавляем путь к ai_ba_agent для использования Gemini engine
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_BA_AGENT_PATH = PROJECT_ROOT / "ai_ba_agent"
if str(AI_BA_AGENT_PATH) not in sys.path:
    sys.path.insert(0, str(AI_BA_AGENT_PATH))

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
            self.parsed = {
                "verdict": "CHANGES_REQUESTED",
                "summary": "Не удалось распарсить ответ LLM",
                "critical_issues": [],
                "suggestions": []
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
        diff: str
    ) -> ReviewResult:
        """
        Анализирует Merge Request через LLM.
        
        Args:
            mr_title: Название MR
            mr_description: Описание MR
            author_name: Имя автора
            target_branch: Целевая ветка
            source_branch: Исходная ветка
            diff: Diff изменений
        
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
            diff=diff
        )
        
        # Отправляем в LLM
        response = self.llm.ask(prompt)
        
        # Парсим результат
        return ReviewResult(response)
    
    def format_review_comment(self, result: ReviewResult) -> str:
        """Форматирует результат анализа в короткий комментарий для GitLab."""
        lines = []
        
        # Вердикт с эмодзи
        if result.verdict == "APPROVE":
            lines.append("## ✅ AI Code Review: APPROVE")
        elif result.verdict == "CHANGES_REQUESTED":
            lines.append("## ❓ AI Code Review: CHANGES_REQUESTED")
        elif result.verdict == "REJECT":
            lines.append("## ❌ AI Code Review: REJECT")
        else:
            lines.append(f"## AI Code Review: {result.verdict}")
        
        lines.append("")
        
        # Объяснение вердикта
        if result.verdict_explanation:
            lines.append(f"**Объяснение:** {result.verdict_explanation}")
            lines.append("")
        
        # Резюме
        if result.summary:
            lines.append(f"**Резюме:** {result.summary}")
            lines.append("")
        
        # Критические проблемы
        if result.critical_issues:
            lines.append("**Критические проблемы:**")
            for issue in result.critical_issues[:5]:  # Максимум 5 проблем
                file = issue.get("file", "unknown")
                line = issue.get("line", "?")
                issue_type = issue.get("type", "error")
                message = issue.get("message", "")
                fix = issue.get("fix", "")
                
                lines.append(f"- `{file}:{line}` ({issue_type}): {message}")
                if fix:
                    lines.append(f"  → Исправление: {fix}")
            lines.append("")
        
        # Рекомендации
        if result.suggestions:
            lines.append("**Рекомендации:**")
            for suggestion in result.suggestions[:3]:  # Максимум 3 рекомендации
                lines.append(f"- {suggestion}")
        
        return "\n".join(lines)
