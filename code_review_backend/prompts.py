"""Промпты для анализа кода через LLM."""

CODE_REVIEW_PROMPT = """Ты — опытный code reviewer. Проанализируй изменения в Merge Request.

**Контекст:**
- Название: {mr_title}
- Описание: {mr_description}
- Автор: {author_name}
- Ветки: {source_branch} → {target_branch}

**Изменения:**
{diff}

**Задача:**
1. Найди критические проблемы: баги, уязвимости, ошибки
2. Оцени качество кода: стиль, читаемость, архитектура
3. Вынеси вердикт: APPROVE / CHANGES_REQUESTED / REJECT

**Формат ответа (JSON, БЕЗ markdown блоков):**
{{
  "verdict": "APPROVE|CHANGES_REQUESTED|REJECT",
  "verdict_explanation": "Краткое объяснение вердикта (1-2 предложения)",
  "summary": "Краткое резюме (1 предложение)",
  "critical_issues": [
    {{
      "file": "путь/к/файлу.py",
      "line": 42,
      "type": "bug|security|error",
      "message": "Краткое описание проблемы",
      "fix": "Как исправить"
    }}
  ],
  "suggestions": [
    "Краткие рекомендации (максимум 3)"
  ]
}}

**Важно:**
- Будь кратким и конкретным
- Указывай только критичные проблемы
- Объясняй вердикт четко и коротко
- Если код хороший — одобри
- Если есть проблемы — объясни что исправить
"""


def format_review_prompt(
    mr_title: str,
    mr_description: str,
    author_name: str,
    target_branch: str,
    source_branch: str,
    diff: str
) -> str:
    """Форматирует промпт для анализа кода."""
    return CODE_REVIEW_PROMPT.format(
        mr_title=mr_title,
        mr_description=mr_description or "(нет описания)",
        author_name=author_name,
        target_branch=target_branch,
        source_branch=source_branch,
        diff=diff
    )
