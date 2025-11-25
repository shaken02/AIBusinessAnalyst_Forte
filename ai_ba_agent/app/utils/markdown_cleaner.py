"""Utilities for cleaning markdown text from LLM artifacts."""

import re


def remove_bullet_points_from_headers(markdown_text: str) -> str:
    """
    Remove bullet points (•, -, *, +) from the beginning of header lines.
    Also remove numbering patterns (1. , 2. , etc.) from headers.
    
    Headers in markdown should start with #, not with bullet points or numbers.
    """
    lines = markdown_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.lstrip()
        
        # Check if this line is a header (starts with #)
        if stripped.startswith('#'):
            # Remove any bullet points before the #
            cleaned = re.sub(r'^[\s]*[•\-\*\+][\s]+', '', line.lstrip())
            # Extract header level and text
            header_match = re.match(r'^(#+)\s*(.*)$', cleaned)
            if header_match:
                header_level = header_match.group(1)
                header_text = header_match.group(2)
                # НЕ удаляем нумерацию - она нужна для структуры документа
                # Просто убираем лишние пробелы
                header_text = header_text.strip()
                cleaned = f"{header_level} {header_text}"
            # Keep original indentation if any, but remove bullet points
            original_indent = len(line) - len(line.lstrip())
            if original_indent > 0:
                cleaned_lines.append(' ' * original_indent + cleaned)
            else:
                cleaned_lines.append(cleaned)
        else:
            # Keep line as is
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def clean_llm_markdown(markdown_text: str) -> str:
    """
    Comprehensive cleaning of markdown text from LLM artifacts.
    
    Removes:
    - Bullet points before headers
    - Extraneous phrases
    - Excessive formatting
    """
    # Remove bullet points from headers
    cleaned = remove_bullet_points_from_headers(markdown_text)
    
    # Remove common LLM endings
    endings = [
        r'Надеюсь это поможет[!\.]*',
        r'Это поможет[!\.]*',
        r'Надеюсь, это поможет[!\.]*',
        r'Пожалуйста, дай знать[^.]*\.',
        r'Если у тебя есть вопросы[^.]*\.',
        r'This will help[!\.]*',
        r'I hope this helps[!\.]*',
    ]
    
    for pattern in endings:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove multiple consecutive asterisks (3+)
    cleaned = re.sub(r'\*{3,}', '', cleaned)
    
    # Clean up multiple spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Max 2 newlines
    
    return cleaned.strip()


__all__ = ["remove_bullet_points_from_headers", "clean_llm_markdown"]

