"""User story generator."""

from __future__ import annotations

from app.core.llm_engine import LLMEngine
from app.utils.markdown_cleaner import clean_llm_markdown


def generate_userstories(context: str, engine: LLMEngine) -> str:
    result = engine.generate_userstories(context)
    # Clean markdown from LLM artifacts (bullet points before headers, etc.)
    return clean_llm_markdown(result)


__all__ = ["generate_userstories"]
