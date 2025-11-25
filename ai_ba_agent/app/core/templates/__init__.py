"""Markdown templates for document generation."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


def load_template(template_name: str) -> str:
    """Load a markdown template file."""
    template_path = TEMPLATES_DIR / f"{template_name}_template.md"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


__all__ = ["load_template", "TEMPLATES_DIR"]


