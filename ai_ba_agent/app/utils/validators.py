"""Validation helpers for dialog input."""

from __future__ import annotations

import re
from typing import Optional

MIN_ANSWER_LENGTH = 5


def normalize_answer(text: str) -> str:
    if not text:
        return ""
    normalized = re.sub(r"\s+", " ", text.strip())
    return normalized


def is_answer_valid(field_key: str, value: Optional[str]) -> bool:
    if not value:
        return False
    return len(value) >= MIN_ANSWER_LENGTH


__all__ = ["normalize_answer", "is_answer_valid", "MIN_ANSWER_LENGTH"]
