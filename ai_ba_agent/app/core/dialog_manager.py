"""Finite-state dialog manager for collecting requirement fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.utils import validators
from app.utils.state import ConversationState, FIELD_METADATA, FIELD_SEQUENCE


@dataclass
class Question:
    field: str
    text: str


class DialogManager:
    def __init__(self, state: ConversationState):
        self.state = state

    def current_field(self) -> Optional[str]:
        for field in FIELD_SEQUENCE:
            if not self.state.answers.get(field):
                return field
        return None

    def get_next_question(self) -> Optional[Question]:
        field = self.current_field()
        if not field:
            return None
        return Question(field=field, text=FIELD_METADATA[field]["question"])

    def accept_answer(self, answer: str) -> Optional[str]:
        field = self.current_field()
        if not field:
            return None
        normalized = validators.normalize_answer(answer)
        if not validators.is_answer_valid(field, normalized):
            raise ValueError("Ответ слишком короткий. Сформулируйте подробнее.")
        self.state.update_field(field, normalized)
        return field

    def is_complete(self) -> bool:
        return self.state.is_complete()


__all__ = ["DialogManager", "Question"]
