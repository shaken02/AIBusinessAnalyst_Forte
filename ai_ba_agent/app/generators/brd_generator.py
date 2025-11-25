"""BRD generator module."""

from __future__ import annotations

from app.core.llm_engine import LLMEngine
from app.utils.markdown_cleaner import clean_llm_markdown


def generate_brd(context: str, engine: LLMEngine) -> str:
    """Return a BRD in Markdown format using the selected LLM engine."""
    result = engine.generate_brd(context)
    # Clean markdown from LLM artifacts (bullet points before headers, etc.)
    return clean_llm_markdown(result)


__all__ = ["generate_brd"]
