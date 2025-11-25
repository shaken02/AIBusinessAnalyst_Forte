"""PDF conversion helpers using ReportLab with full Unicode support."""

from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    SimpleDocTemplate,
)


# ReportLab's built-in Helvetica doesn't support Cyrillic well
# We need to register a TTF font that supports Unicode/Cyrillic
FONT_REGISTERED = False
CYRILLIC_FONT_NAME = 'Helvetica'  # Fallback

def _register_cyrillic_font():
    """Try to register a font that supports Cyrillic characters."""
    global FONT_REGISTERED, CYRILLIC_FONT_NAME
    
    if FONT_REGISTERED:
        return
    
    import os
    font_paths = [
        # macOS system fonts (Arial supports Cyrillic)
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/Library/Fonts/Arial.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        # Linux common fonts
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                from reportlab.pdfbase.ttfonts import TTFont
                # Try to register the font
                try:
                    # Register normal and bold variants
                    font_base_name = 'CyrillicFont'
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    
                    # Register the font
                    pdfmetrics.registerFont(TTFont(font_base_name, font_path))
                    
                    # Try to find bold version
                    bold_font_path = font_path.replace('.ttf', ' Bold.ttf').replace('-Regular', '-Bold')
                    bold_registered = False
                    if os.path.exists(bold_font_path):
                        pdfmetrics.registerFont(TTFont(f'{font_base_name}-Bold', bold_font_path))
                        bold_registered = True
                    
                    # Try to find italic version
                    italic_font_path = font_path.replace('.ttf', ' Italic.ttf').replace('-Regular', '-Italic')
                    italic_registered = False
                    if os.path.exists(italic_font_path):
                        pdfmetrics.registerFont(TTFont(f'{font_base_name}-Italic', italic_font_path))
                        italic_registered = True
                    
                    # Register font family with available variants
                    if bold_registered and italic_registered:
                        pdfmetrics.registerFontFamily(font_base_name, 
                                                      normal=font_base_name, 
                                                      bold=f'{font_base_name}-Bold',
                                                      italic=f'{font_base_name}-Italic',
                                                      boldItalic=font_base_name)
                    elif bold_registered:
                        pdfmetrics.registerFontFamily(font_base_name, 
                                                      normal=font_base_name, 
                                                      bold=f'{font_base_name}-Bold')
                    elif italic_registered:
                        pdfmetrics.registerFontFamily(font_base_name, 
                                                      normal=font_base_name, 
                                                      italic=f'{font_base_name}-Italic')
                    else:
                        # Use same font for all variants
                        pdfmetrics.registerFontFamily(font_base_name, 
                                                      normal=font_base_name, 
                                                      bold=font_base_name)
                    CYRILLIC_FONT_NAME = font_base_name
                    FONT_REGISTERED = True
                    print(f"Registered Cyrillic font: {font_base_name} from {font_path}")
                    return
                except Exception as e:
                    # Font file exists but might not be valid TTF
                    print(f"Warning: Could not register font {font_path}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            except Exception as e:
                continue
    
    # If no font found, we'll use Helvetica and hope it works
    # ReportLab should handle encoding, but it might show squares for unsupported chars
    FONT_REGISTERED = True

# Register font on import
_register_cyrillic_font()


def _create_title_page(story: List, project_name: str) -> None:
    """Create a professional title page with project information."""
    styles = getSampleStyleSheet()
    
    # Title page with better design
    # Add colored background rectangle
    from reportlab.platypus import Table, TableStyle, Spacer
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    
    # Clean project name from LLM artifacts
    cleaned_name = _clean_llm_text(project_name)
    
    # Escape HTML special characters in project name
    cleaned_name_html = cleaned_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Calculate available width for title (page width minus margins)
    available_width = A4[0] - 40*mm  # Reduced margins to fit more text
    
    # Calculate font size dynamically based on text length and available width
    # Very aggressive scaling - we prioritize showing full text over font size
    name_length = len(cleaned_name)
    text_available_width = available_width - 20*mm  # Reduced padding to fit more text
    
    # Calculate optimal font size to fit text
    # Approximate: chars per line = (width in points) / (font_size * 0.6 for Cyrillic)
    # We want text to fit comfortably
    
    # Start with base calculation - assume we need multiple lines
    # Average Cyrillic character width is about 0.6 * font_size
    # So: chars_per_line ≈ (text_available_width_pt) / (font_size * 0.6)
    # We want: name_length <= chars_per_line * lines, where lines can be multiple
    
    # More aggressive scaling - smaller font ensures text fits, but allow more lines
    # Calculate based on available width to ensure full text is visible
    text_width_pt = text_available_width / mm * 2.83465  # Convert mm to points (1mm = 2.83465pt)
    
    # Allow up to 8 lines for very long titles
    max_lines = 8
    chars_per_line_est = max(10, name_length / max_lines)
    
    # Calculate font size to fit text: chars_per_line ≈ (width_pt) / (font_size * 0.6)
    # So: font_size ≈ (width_pt) / (chars_per_line * 0.6)
    calculated_font_size = (text_width_pt) / (chars_per_line_est * 0.6)
    
    # Clamp font size between reasonable bounds
    title_font_size = max(8, min(28, calculated_font_size))
    
    # For very short names, use larger font
    if name_length <= 30:
        title_font_size = max(title_font_size, 24)
    elif name_length <= 50:
        title_font_size = max(title_font_size, 20)
    elif name_length <= 70:
        title_font_size = max(title_font_size, 16)
    
    # Create paragraph style with proper wrapping
    # Don't use nested para tags - use simple font tag with alignment attribute
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=title_font_size,
        textColor=colors.white,
        spaceAfter=0,
        spaceBefore=0,
        alignment=1,  # Center
        fontName=CYRILLIC_FONT_NAME,
        leading=title_font_size * 1.6,  # Generous line spacing for multi-line text
        wordWrap='LTR',  # Enable word wrapping
        leftIndent=0,
        rightIndent=0,
        # Don't set width here - let it use available width from table
    )
    
    # Use simple HTML format without nested para tags
    # Just use font tag - ReportLab will handle wrapping based on table width
    title_para = Paragraph(
        f'<font name="{CYRILLIC_FONT_NAME}" size="{title_font_size}" color="white">{cleaned_name_html}</font>',
        title_style
    )
    
    # Calculate estimated height based on text length and font size
    # More accurate calculation
    chars_per_line = max(15, int(text_available_width / mm * 2.83465 / (title_font_size * 0.6)))  # Convert mm to points
    estimated_lines = max(1, (name_length + chars_per_line - 1) // chars_per_line)  # Ceiling division
    min_row_height = estimated_lines * (title_font_size * 1.6) + 50*mm  # Add padding with generous spacing
    
    # Create table WITHOUT fixed row height - let it auto-expand
    # But set minimum to ensure enough space
    header_table = Table(
        [[title_para]],
        colWidths=[available_width],
        # Don't set rowHeights - let ReportLab calculate based on content
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B1538')),  # Dark red/cherry background (ForteBank brand color)
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 25*mm),  # Generous padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 25*mm),  # Generous padding
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 25*mm))
    
    # Project info section - cleaner design
    # Use Paragraph for long project name to enable wrapping
    info_label_style = ParagraphStyle(
        'InfoLabel',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        fontName=CYRILLIC_FONT_NAME,
        alignment=0,  # Left
    )
    
    info_value_style = ParagraphStyle(
        'InfoValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1a1a1a'),
        fontName=CYRILLIC_FONT_NAME,
        alignment=0,  # Left
        wordWrap='LTR',  # Enable word wrapping
    )
    
    info_data = [
        [Paragraph('Название проекта:', info_label_style), Paragraph(cleaned_name_html, info_value_style)],
        [Paragraph('Создано:', info_label_style), Paragraph('AI Business Analyst', info_value_style)],
        [Paragraph('Дата:', info_label_style), Paragraph(datetime.now().strftime("%d.%m.%Y"), info_value_style)],
        [Paragraph('Версия:', info_label_style), Paragraph('#1', info_value_style)],
    ]
    
    info_table = Table(info_data, colWidths=[50*mm, 140*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(info_table)


def _clean_llm_text(text: str) -> str:
    """Clean LLM output from unnecessary phrases."""
    import re
    
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
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove multiple consecutive asterisks (3+)
    text = re.sub(r'\*{3,}', '', text)
    
    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def _convert_markdown_to_html(text: str) -> str:
    """Convert markdown formatting to HTML for ReportLab Paragraph."""
    import re
    
    # Clean LLM text first
    text = _clean_llm_text(text)
    
    # Escape HTML special characters first
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Remove excessive bold markers (leave only single **text** for actual emphasis)
    # Remove standalone ** that don't form pairs
    text = re.sub(r'\*\*([^*]{1,2})\*\*', r'\1', text)  # Remove **a** where a is 1-2 chars (likely formatting error)
    
    # Convert markdown bold **text** to <b>text</b> only for meaningful text (3+ chars)
    text = re.sub(r'\*\*([^*]{3,}?)\*\*', r'<b>\1</b>', text)
    
    # Remove remaining unpaired **
    text = re.sub(r'\*\*+', '', text)
    
    # Convert markdown italic *text* to <i>text</i> (but not if it's part of bold)
    text = re.sub(r'(?<!\*)\*([^*]{3,}?)\*(?!\*)', r'<i>\1</i>', text)
    
    # Remove remaining unpaired *
    text = re.sub(r'(?<![*])\*(?![*])', '', text)
    
    return text


def _parse_markdown_table(lines: List[str], start_idx: int) -> tuple[List[List[str]], int]:
    """Parse markdown table from lines starting at start_idx.
    
    Preserves all cells, including empty ones, to maintain table structure.
    """
    table_data = []
    idx = start_idx
    
    # Determine number of columns from header
    num_columns = 0
    
    # Parse header
    if idx < len(lines):
        # Split by |, remove first and last empty strings (from leading/trailing |)
        cells = lines[idx].split('|')
        # Remove first and last if empty (markdown tables start and end with |)
        if cells and not cells[0].strip():
            cells = cells[1:]
        if cells and not cells[-1].strip():
            cells = cells[:-1]
        # Strip all cells but keep empty ones - convert empty strings to single space
        header = [cell.strip() if cell.strip() else '' for cell in cells]
        num_columns = len(header)
        if header:
            table_data.append(header)
        idx += 1
    
    # Skip separator line (|---|---|)
    if idx < len(lines) and re.match(r'^\|[\s\-\|:]+\|$', lines[idx]):
        idx += 1
    
    # Parse rows
    while idx < len(lines):
        line = lines[idx].strip()
        if not line or not line.startswith('|'):
            break
        # Split by |, remove first and last empty strings (from leading/trailing |)
        cells = line.split('|')
        # Remove first and last if empty (markdown tables start and end with |)
        if cells and not cells[0].strip():
            cells = cells[1:]
        if cells and not cells[-1].strip():
            cells = cells[:-1]
        # Strip all cells but keep empty ones - pad to match header columns
        row = [cell.strip() if cell.strip() else '' for cell in cells]
        # Pad row to match header if needed (in case some cells are missing)
        while len(row) < num_columns:
            row.append('')
        # Truncate if too long (shouldn't happen, but just in case)
        row = row[:num_columns]
        if row:
            table_data.append(row)
        idx += 1
    
    return table_data, idx


def _render_table(story: List, table_data: List[List[str]]) -> None:
    """Render a markdown table in PDF."""
    if not table_data:
        return
    
    # Calculate table width to fit page
    page_width = A4[0] - 30*mm  # Page width minus margins
    num_cols = len(table_data[0]) if table_data else 1
    
    # Create styles for table cells
    styles = getSampleStyleSheet()
    header_cell_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        fontName=CYRILLIC_FONT_NAME,
        alignment=0,  # Left
        wordWrap='LTR',  # Enable word wrapping
        leading=12,
    )
    
    data_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        fontName=CYRILLIC_FONT_NAME,
        alignment=0,  # Left
        wordWrap='LTR',  # Enable word wrapping for long text
        leading=12,
    )
    
    # Convert table data to Paragraph objects for proper text wrapping
    para_data = []
    for row_idx, row in enumerate(table_data):
        para_row = []
        for cell in row:
            # Clean cell text from LLM artifacts
            cleaned_cell = _clean_llm_text(str(cell))
            # Escape HTML special characters
            cleaned_cell_html = _convert_markdown_to_html(cleaned_cell)
            # Use header style for first row, data style for others
            cell_style = header_cell_style if row_idx == 0 else data_cell_style
            para_row.append(Paragraph(cleaned_cell_html, cell_style))
        para_data.append(para_row)
    
    # Create table with calculated column widths
    col_widths = [page_width / num_cols] * num_cols
    pdf_table = Table(para_data, colWidths=col_widths)
    
    # Style the table - less bold, better design
    style = TableStyle([
        # Header row - subtle background
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows - normal font weight
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        
        # Grid - subtle
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top align for multi-line cells
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ])
    
    pdf_table.setStyle(style)
    story.append(pdf_table)
    story.append(Spacer(1, 6*mm))


# Global heading counters for document-wide hierarchical numbering
# These persist across all sections to maintain continuous numbering
_document_heading_counters = [0, 0, 0, 0]  # For #, ##, ###, ####


def _add_section(story: List, section_title: str, content: str, heading_counters: List[int] = None) -> None:
    """Add a section with formatted content and hierarchical numbering.
    
    Args:
        story: List to append PDF elements to
        section_title: Title of the section (not numbered, just displayed)
        content: Markdown content of the section
        heading_counters: Optional list to use for numbering. If None, uses global counters.
    """
    global _document_heading_counters
    
    # Use provided counters or global ones
    if heading_counters is None:
        heading_counters = _document_heading_counters
    
    styles = getSampleStyleSheet()
    
    # Don't add section title here - it's already in the content as a heading
    # The section_title parameter is just for reference, we don't display it separately
    
    # Process content - italic (not bold), better spacing
    normal_style = ParagraphStyle(
        'NormalContent',
        parent=styles['Normal'],
        fontSize=10.5,
        textColor=colors.HexColor('#2a2a2a'),
        spaceAfter=8,
        leftIndent=0,
        rightIndent=0,
        fontName=CYRILLIC_FONT_NAME,
        leading=14,  # Line spacing
    )
    
    # Get bold font name if available
    bold_font_name = CYRILLIC_FONT_NAME
    try:
        if f'{CYRILLIC_FONT_NAME}-Bold' in pdfmetrics.getRegisteredFontNames():
            bold_font_name = f'{CYRILLIC_FONT_NAME}-Bold'
    except:
        pass
    
    # Heading styles with numbering
    h1_style = ParagraphStyle(
        'H1Content',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f1f1f'),
        spaceAfter=8,
        spaceBefore=12,
        fontName=bold_font_name,
        leftIndent=0,
    )
    
    h2_style = ParagraphStyle(
        'H2Content',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#252525'),
        spaceAfter=6,
        spaceBefore=10,
        fontName=bold_font_name,
        leftIndent=0,
    )
    
    h3_style = ParagraphStyle(
        'H3Content',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#252525'),
        spaceAfter=6,
        spaceBefore=10,
        fontName=bold_font_name,
        leftIndent=0,
    )
    
    h4_style = ParagraphStyle(
        'H4Content',
        parent=styles['Heading4'],
        fontSize=11,
        textColor=colors.HexColor('#252525'),
        spaceAfter=6,
        spaceBefore=10,
        fontName=bold_font_name,
        leftIndent=0,
    )
    
    # List styles
    list_style = ParagraphStyle(
        'ListContent',
        parent=normal_style,
        leftIndent=15,
        bulletIndent=8,
        fontName=CYRILLIC_FONT_NAME,
        spaceAfter=4,
    )
    
    numbered_list_style = ParagraphStyle(
        'NumberedListContent',
        parent=normal_style,
        leftIndent=15,
        bulletIndent=8,
        fontName=CYRILLIC_FONT_NAME,
        spaceAfter=4,
    )
    
    lines = content.split('\n')
    idx = 0
    
    def get_heading_number(level: int) -> str:
        """Generate hierarchical heading number (1, 1.1, 1.1.1, etc.)."""
        nonlocal heading_counters
        level_idx = level - 1  # level 1 = index 0
        
        # Increment counter for this level
        heading_counters[level_idx] += 1
        # Reset deeper level counters
        for i in range(level_idx + 1, len(heading_counters)):
            heading_counters[i] = 0
        
        # Build number string
        number_parts = []
        for i in range(level_idx + 1):
            if heading_counters[i] > 0:
                number_parts.append(str(heading_counters[i]))
        
        return '.'.join(number_parts)
    
    def is_numbered_list(line: str) -> bool:
        """Check if line starts with a numbered list marker (1., 2., 1), etc.)."""
        line = line.strip()
        # Match patterns like "1.", "2.", "1)", "2)", "1. ", etc.
        return bool(re.match(r'^\d+[.)]\s+', line))
    
    def extract_numbered_list_item(line: str) -> tuple[int, str]:
        """Extract number and text from numbered list item."""
        match = re.match(r'^(\d+)[.)]\s+(.*)$', line.strip())
        if match:
            return int(match.group(1)), match.group(2)
        return 0, line
    
    def is_likely_heading(text: str) -> bool:
        """Check if text looks like a heading (short, no ending punctuation usually)."""
        text = text.strip()
        # Remove bullet points and markdown
        text = text.lstrip('•').lstrip('#').lstrip('-*+').strip()
        # Heading-like if: short (< 80 chars), no ending punctuation, or ends with colon
        return len(text) < 80 and (not text.endswith('.') or text.endswith(':') or text.endswith(':'))
    
    def remove_numbering_from_text(text: str) -> str:
        """Keep numbering patterns - DO NOT remove them."""
        # НЕ удаляем нумерацию - она нужна для структуры документа
        return text.strip()
    
    while idx < len(lines):
        line = lines[idx].strip()
        
        if not line:
            story.append(Spacer(1, 4*mm))
            idx += 1
            continue
        
        # Check if this is a markdown table
        if line.startswith('|') and '|' in line[1:]:
            table_data, next_idx = _parse_markdown_table(lines, idx)
            if table_data:
                _render_table(story, table_data)
                idx = next_idx
                continue
        
        # Remove bullet points from lines that look like headings
        cleaned_line_for_check = line.lstrip('•').lstrip('#').strip()
        
        # Remove bullet point (•) from beginning if it looks like a heading
        original_line = line
        if line.startswith('•') and is_likely_heading(line[1:]):
            line = line[1:].strip()
        
        # Process markdown headers - сохраняем нумерацию из LLM
        if line.startswith('####'):
            text = line.lstrip('#').strip()
            # Сохраняем нумерацию - НЕ удаляем
            text = _clean_llm_text(text)
            text = text.replace('**', '').replace('*', '')
            text = _convert_markdown_to_html(text)
            text = f'<b>{text}</b>' if not text.startswith('<b>') else text
            story.append(Paragraph(text, h4_style))
            idx += 1
            continue
        elif line.startswith('###'):
            text = line.lstrip('#').strip()
            # Сохраняем нумерацию - НЕ удаляем
            text = _clean_llm_text(text)
            text = text.replace('**', '').replace('*', '')
            text = _convert_markdown_to_html(text)
            text = f'<b>{text}</b>' if not text.startswith('<b>') else text
            story.append(Paragraph(text, h3_style))
            idx += 1
            continue
        elif line.startswith('##'):
            text = line.lstrip('#').strip()
            # Сохраняем нумерацию - НЕ удаляем
            text = _clean_llm_text(text)
            text = text.replace('**', '').replace('*', '')
            text = _convert_markdown_to_html(text)
            text = f'<b>{text}</b>' if not text.startswith('<b>') else text
            story.append(Paragraph(text, h2_style))
            idx += 1
            continue
        elif line.startswith('#'):
            text = line.lstrip('#').strip()
            # Сохраняем нумерацию - НЕ удаляем
            text = _clean_llm_text(text)
            text = text.replace('**', '').replace('*', '')
            text = _convert_markdown_to_html(text)
            text = f'<b>{text}</b>' if not text.startswith('<b>') else text
            story.append(Paragraph(text, h1_style))
            idx += 1
            continue
        
        # Check if line that starts with bullet point but is NOT a heading should be treated as heading
        # (e.g., "• Business Requirements Document (BRD)" should be a heading, not a list item)
        if original_line.startswith('•') and is_likely_heading(original_line[1:]) and not line.startswith('-') and not line.startswith('*') and not line.startswith('+'):
            # Treat as heading level 1 if it looks like a main section title
            text = original_line[1:].strip()
            # Сохраняем нумерацию - НЕ удаляем
            text = _clean_llm_text(text)
            text = text.replace('**', '').replace('*', '')
            text = _convert_markdown_to_html(text)
            text = f'<b>{text}</b>' if not text.startswith('<b>') else text
            story.append(Paragraph(text, h1_style))
            idx += 1
            continue
        
        # Process numbered lists (1., 2., 3., etc.)
        if is_numbered_list(line):
            _, text = extract_numbered_list_item(line)
            text = _convert_markdown_to_html(text)
            if not text.strip().startswith('<b>'):
                text = f'<i>{text}</i>'
            else:
                text = f'<i>{text}</i>'
            # Get the number from the line
            num = extract_numbered_list_item(line)[0]
            story.append(Paragraph(f'{num}. {text}', numbered_list_style))
            idx += 1
            continue
        
        # Process unnumbered lists (-, *, +, •)
        # But skip if it looks like a heading (already processed above)
        if (line.startswith('-') or line.startswith('*') or line.startswith('+') or 
            (line.startswith('•') and not is_likely_heading(line[1:]))):
            text = line.lstrip('-*+•').strip()
            # Convert markdown bold to HTML properly
            text = _convert_markdown_to_html(text)
            if not text.strip().startswith('<b>'):
                text = f'<i>{text}</i>'
            else:
                text = f'<i>{text}</i>'
            story.append(Paragraph(f'• {text}', list_style))
            idx += 1
            continue
        
        # Process regular text
        cleaned_line = _clean_llm_text(line)
        
        if not cleaned_line.strip():
            idx += 1
            continue
        
        text = _convert_markdown_to_html(cleaned_line)
        
        if not text.strip() or text.strip() in ['<b></b>', '<i></i>', '&nbsp;']:
            idx += 1
            continue
        
        # Wrap regular text in <i> tags for italic
        if not text.strip().startswith('<b>') and not text.strip().startswith('<i>'):
            text = f'<i>{text}</i>'
        elif '<b>' in text and '</b>' in text:
            text = f'<i>{text}</i>'
        
        story.append(Paragraph(text, normal_style))
        idx += 1
    
    story.append(Spacer(1, 10*mm))


def markdown_to_pdf_bytes(sections: Dict[str, str], project_name: str = "Business Requirements Document") -> bytes:
    """Generate professional PDF from markdown sections with full Unicode support."""
    global _document_heading_counters
    
    # Reset global heading counters for new document
    _document_heading_counters = [0, 0, 0, 0]
    
    from reportlab.platypus import Image as RLImage
    
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Create title page
    _create_title_page(story, project_name)
    story.append(PageBreak())
    
    # Add each document section
    for title, content in sections.items():
        if title == "PlantUML":
            # Special handling for PlantUML - render as image
            from app.utils.plantuml_renderer import render_plantuml_to_png
            from reportlab.platypus import Image as RLImage
            
            # Add section title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#282828'),
                spaceAfter=6,
                fontName=CYRILLIC_FONT_NAME,
            )
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 4*mm))
            
            # Try to render PlantUML diagram as image
            png_bytes = render_plantuml_to_png(content)
            if png_bytes:
                try:
                    from PIL import Image as PILImage
                    
                    # Calculate available dimensions
                    page_width = A4[0] - 30*mm  # Page width minus margins
                    page_height = A4[1] - 60*mm  # Page height minus margins (top + bottom)
                    
                    # Get actual image dimensions
                    img_buffer = io.BytesIO(png_bytes)
                    pil_img = PILImage.open(img_buffer)
                    img_width_pt, img_height_pt = pil_img.size
                    
                    # Convert pixels to points (1 pixel = 0.75 points approximately)
                    # But better to use actual DPI - PIL images usually 72 DPI
                    # So 1 pixel = 1 point at 72 DPI
                    img_width_points = img_width_pt
                    img_height_points = img_height_pt
                    
                    # Calculate scaling factors
                    width_scale = page_width / img_width_points if img_width_points > 0 else 1
                    height_scale = page_height / img_height_points if img_height_points > 0 else 1
                    
                    # Use the smaller scale to ensure image fits both dimensions
                    scale = min(width_scale, height_scale, 1.0)  # Don't enlarge, only shrink
                    
                    # Calculate final dimensions
                    final_width = img_width_points * scale
                    final_height = img_height_points * scale
                    
                    # Create image from bytes with proper dimensions
                    img_buffer.seek(0)  # Reset buffer position
                    img = RLImage(img_buffer, width=final_width, height=final_height)
                    story.append(img)
                    story.append(Spacer(1, 4*mm))
                except Exception as e:
                    # Fallback message if image insertion fails
                    error_style = ParagraphStyle(
                        'Error',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.HexColor('#999999'),
                        fontName=CYRILLIC_FONT_NAME,
                    )
                    story.append(Paragraph(f"<i>Не удалось вставить диаграмму: {e}</i>", error_style))
            else:
                # Fallback message if rendering failed
                error_style = ParagraphStyle(
                    'Error',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#999999'),
                    fontName=CYRILLIC_FONT_NAME,
                )
                story.append(Paragraph("<i>Не удалось сгенерировать диаграмму для PDF</i>", error_style))
        else:
            _add_section(story, title, content)
        
        if title != list(sections.keys())[-1]:  # Don't add page break after last section
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.read()


__all__ = ["markdown_to_pdf_bytes"]
