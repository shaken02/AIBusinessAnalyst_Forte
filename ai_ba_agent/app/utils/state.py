"""State container for the AI Business Analyst dialog."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

FIELD_SEQUENCE: List[str] = [
    "description",
    "problem",
    "goal",
    "stakeholders",
    "roles",
    "scope",
    "out_of_scope",
    "kpi",
    "business_rules",
    "constraints",
    "risks",
    "assumptions",
    "nfr",
    "process_description",
]

FIELD_METADATA: Dict[str, Dict[str, str]] = {
    "goal": {
        "label": "Цель",
        "question": "Какова ключевая цель инициативы?",
    },
    "problem": {
        "label": "Проблема",
        "question": "Какую проблему или боль клиента решает продукт?",
    },
    "description": {
        "label": "Описание",
        "question": "Опишите продукт / решение простыми словами.",
    },
    "stakeholders": {
        "label": "Стейкхолдеры",
        "question": "Кто основные заинтересованные стороны?",
    },
    "roles": {
        "label": "Роли",
        "question": "Какие роли/персоны задействованы в процессе?",
    },
    "scope": {
        "label": "В рамках",
        "question": "Что входит в зону ответственности проекта?",
    },
    "out_of_scope": {
        "label": "Вне рамок",
        "question": "Что явно исключено из проекта?",
    },
    "kpi": {
        "label": "KPI",
        "question": "Какие ключевые метрики успеха?",
    },
    "business_rules": {
        "label": "Бизнес-правила",
        "question": "Опишите важные правила/политики.",
    },
    "constraints": {
        "label": "Ограничения",
        "question": "Какие технические/организационные ограничения существуют?",
    },
    "risks": {
        "label": "Риски",
        "question": "Какие основные риски вы видите?",
    },
    "assumptions": {
        "label": "Допущения",
        "question": "Какие допущения необходимо зафиксировать?",
    },
    "nfr": {
        "label": "Нефункциональные требования",
        "question": "Есть ли NFR (производительность, безопасность, UX)?",
    },
    "process_description": {
        "label": "Описание процесса",
        "question": "Опишите ключевые шаги процесса или сценарий конца-в-конец.",
    },
}


def field_label(field_key: str) -> str:
    return FIELD_METADATA.get(field_key, {}).get("label", field_key.title())


@dataclass
class ConversationState:
    """Mutable dialog state stored in Streamlit session."""

    answers: Dict[str, str] = field(default_factory=dict)
    history: List[Tuple[str, str]] = field(default_factory=list)
    generated_bundle_id: Optional[str] = None

    def reset(self) -> None:
        self.answers.clear()
        self.history.clear()
        self.generated_bundle_id = None

    def update_field(self, field_key: str, value: str) -> None:
        self.answers[field_key] = value
        self.history.append((field_key, value))

    def get_missing_fields(self) -> List[str]:
        """Get list of fields that are not filled or contain only empty/whitespace."""
        missing = []
        for field in FIELD_SEQUENCE:
            value = self.answers.get(field, "").strip()
            # Field is missing if it's empty, None, or contains only placeholder text
            if not value or value in ["—", "-", "не указано", "не заполнено", ""]:
                missing.append(field)
        return missing

    def is_complete(self) -> bool:
        return not self.get_missing_fields()

    def as_markdown_context(self) -> str:
        sections: List[str] = []
        for field in FIELD_SEQUENCE:
            label = field_label(field)
            value = self.answers.get(field, "—")
            sections.append(f"### {label}\n{value or '—'}")
        return "\n\n".join(sections)

    def progress_ratio(self) -> float:
        total = len(FIELD_SEQUENCE)
        filled = total - len(self.get_missing_fields())
        if total == 0:
            return 0.0
        return filled / total


__all__ = [
    "ConversationState",
    "FIELD_SEQUENCE",
    "FIELD_METADATA",
    "field_label",
]
