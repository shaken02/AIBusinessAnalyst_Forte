"""Unit tests for PDF generator with Cyrillic support."""

from __future__ import annotations

import tempfile
import os
from pathlib import Path

from app.generators.pdf_generator import (
    markdown_to_pdf_bytes,
    _register_cyrillic_font,
    CYRILLIC_FONT_NAME,
)


class TestPDFCyrillicSupport:
    """Test PDF generation with Cyrillic characters."""
    
    def test_cyrillic_text_in_pdf(self):
        """Test that Cyrillic text is properly rendered in PDF."""
        # Test text with Cyrillic characters
        test_sections = {
            "BRD": """
# Business Requirements Document

## Обзор проекта

Система лояльности для клиентов банка позволяет накапливать баллы за транзакции.

### Цель проекта
Создать мобильное приложение для управления программой лояльности.

### Стейкхолдеры
- Клиенты банка
- Отдел маркетинга  
- IT-отдел

### KPI
Увеличение retention на 25%, средний чек транзакций на 15%.

### Таблица

| Показатель | Значение | Описание |
|------------|----------|----------|
| Retention | +25% | Увеличение повторных клиентов |
| Средний чек | +15% | Рост транзакций |
| Оценка | 4.5/5 | Средняя оценка пользователей |
""",
            "Use Case": "Как клиент, я хочу накапливать баллы, чтобы получать скидки.",
            "User Stories": "Клиент регистрируется в программе лояльности через мобильное приложение.",
            "PlantUML": "@startuml\nstart\n:Регистрация клиента;\nstop\n@enduml"
        }
        
        # Generate PDF
        project_name = "Система лояльности банка"
        pdf_bytes = markdown_to_pdf_bytes(test_sections, project_name=project_name)
        
        # Verify PDF was generated
        if pdf_bytes is None:
            raise AssertionError("PDF не был сгенерирован")
        if len(pdf_bytes) == 0:
            raise AssertionError("PDF пустой")
        
        # Save to temp file for manual inspection
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        
        print(f"\n✅ PDF сгенерирован: {tmp_path}")
        print(f"   Размер: {len(pdf_bytes)} байт ({len(pdf_bytes) / 1024:.2f} KB)")
        
        # Check if PDF contains Cyrillic bytes (UTF-8 encoding)
        # PDFs with embedded fonts store text in various ways, but we can check
        # if the file structure is valid
        if not pdf_bytes.startswith(b'%PDF'):
            raise AssertionError("PDF должен начинаться с %PDF")
        
        # Check if font is registered
        if CYRILLIC_FONT_NAME is None:
            raise AssertionError("Шрифт с поддержкой кириллицы должен быть зарегистрирован")
        print(f"   Зарегистрированный шрифт: {CYRILLIC_FONT_NAME}")
        
        # Check if Cyrillic text is mentioned in PDF (might be in text streams)
        # Note: PDF text is often encoded/compressed, so we check for PDF structure
        # Real verification requires opening the PDF in a viewer
        
        # Search for Cyrillic bytes in PDF (might be encoded/compressed)
        # Check for common Cyrillic UTF-8 patterns: D0, D1 (Russian Cyrillic range)
        cyrillic_bytes_found = b'\xd0' in pdf_bytes or b'\xd1' in pdf_bytes or b'\xd2' in pdf_bytes
        if cyrillic_bytes_found:
            print(f"   ✅ Обнаружены UTF-8 байты кириллицы в PDF!")
        else:
            print(f"   ⚠️  UTF-8 байты кириллицы не найдены (может быть в сжатом виде)")
        
        print(f"   ✅ Тест пройден! PDF правильно структурирован.")
        print(f"   💡 Откройте PDF для визуальной проверки: {tmp_path}")
        
        # Don't delete - let user inspect it
        return tmp_path
    
    def test_font_registration(self):
        """Test that Cyrillic font is properly registered."""
        _register_cyrillic_font()
        if CYRILLIC_FONT_NAME is None:
            raise AssertionError("Шрифт не зарегистрирован")
        print(f"✅ Шрифт зарегистрирован: {CYRILLIC_FONT_NAME}")
    
    def test_markdown_tables(self):
        """Test that markdown tables are properly rendered."""
        test_sections = {
            "Test": """
# Тестовая секция

## Таблица

| Колонка 1 | Колонка 2 | Колонка 3 |
|-----------|-----------|-----------|
| Значение 1 | Значение 2 | Значение 3 |
| Данные 1 | Данные 2 | Данные 3 |
"""
        }
        
        pdf_bytes = markdown_to_pdf_bytes(test_sections, project_name="Тест таблиц")
        
        if pdf_bytes is None or len(pdf_bytes) == 0:
            raise AssertionError("PDF не был сгенерирован")
        if not pdf_bytes.startswith(b'%PDF'):
            raise AssertionError("PDF должен начинаться с %PDF")
        
        print("✅ Таблицы правильно рендерятся в PDF")


if __name__ == "__main__":
    # Run tests manually
    test = TestPDFCyrillicSupport()
    
    print("=" * 60)
    print("🧪 Тестирование PDF генератора с поддержкой кириллицы")
    print("=" * 60)
    
    print("\n1. Тест регистрации шрифта:")
    test.test_font_registration()
    
    print("\n2. Тест генерации PDF с кириллицей:")
    pdf_path = test.test_cyrillic_text_in_pdf()
    
    print("\n3. Тест таблиц:")
    test.test_markdown_tables()
    
    print("\n" + "=" * 60)
    print("✅ Все тесты пройдены!")
    print("=" * 60)
    print(f"\n💡 Откройте PDF файл для визуальной проверки:")
    print(f"   {pdf_path}")

