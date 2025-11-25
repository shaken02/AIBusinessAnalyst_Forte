"""Unit tests for PlantUML visualization."""

from __future__ import annotations

import base64
import requests
from typing import Optional


def test_plantuml_encoding(plantuml_code: str) -> tuple[str, bool]:
    """
    Test PlantUML encoding and return URL and success status.
    
    Args:
        plantuml_code: PlantUML code to encode
        
    Returns:
        Tuple of (URL, success_status)
    """
    # Ensure @startuml/@enduml are present
    code = plantuml_code.strip()
    if not code.startswith('@startuml'):
        code = f"@startuml\n{code}"
    if not code.endswith('@enduml'):
        code = f"{code}\n@enduml"
    
    # Method 1: Simple base64 encoding (UTF-8)
    encoded = base64.b64encode(code.encode('utf-8')).decode('utf-8')
    # Convert to URL-safe format
    encoded = encoded.translate(str.maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    )).rstrip('=')
    
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"
    
    # Test if URL works
    try:
        response = requests.head(url, timeout=10)
        return url, response.status_code == 200
    except Exception as e:
        print(f"   ⚠️  Ошибка при проверке URL: {e}")
        return url, False


def test_plantuml_defalte_encoding(plantuml_code: str) -> tuple[str, bool]:
    """
    Test PlantUML encoding with DEFLATE compression.
    
    Args:
        plantuml_code: PlantUML code to encode
        
    Returns:
        Tuple of (URL, success_status)
    """
    import zlib
    
    code = plantuml_code.strip()
    if not code.startswith('@startuml'):
        code = f"@startuml\n{code}"
    if not code.endswith('@enduml'):
        code = f"{code}\n@enduml"
    
    # DEFLATE compression
    compressed = zlib.compress(code.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('utf-8')
    encoded = encoded.replace('+', '-').replace('/', '_').rstrip('=')
    encoded = '~1' + encoded
    
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"
    
    # Test if URL works
    try:
        response = requests.head(url, timeout=10)
        return url, response.status_code == 200
    except Exception as e:
        print(f"   ⚠️  Ошибка при проверке URL: {e}")
        return url, False


class TestPlantUMLVisualization:
    """Test PlantUML diagram visualization."""
    
    def test_simple_diagram(self):
        """Test simple PlantUML activity diagram."""
        plantuml_code = """
@startuml
start
:Регистрация клиента;
:Начисление баллов;
stop
@enduml
"""
        
        print("\n🧪 Тест простой диаграммы:")
        print(f"   Код: {len(plantuml_code.strip())} символов")
        
        # Test UTF-8 encoding
        url1, success1 = test_plantuml_encoding(plantuml_code)
        print(f"   UTF-8 метод: {'✅ Работает' if success1 else '❌ Не работает'}")
        print(f"   URL: {url1[:80]}...")
        
        # Test DEFLATE encoding
        url2, success2 = test_plantuml_defalte_encoding(plantuml_code)
        print(f"   DEFLATE метод: {'✅ Работает' if success2 else '❌ Не работает'}")
        print(f"   URL: {url2[:80]}...")
        
        assert success1 or success2, "Хотя бы один метод кодирования должен работать"
        return url1 if success1 else url2
    
    def test_complex_diagram_with_cyrillic(self):
        """Test complex PlantUML diagram with Cyrillic text."""
        plantuml_code = """
@startuml
title Процесс оплаты с начислением баллов

start
:Клиент совершает покупку;
:Процессинг подтверждает транзакцию;
if (Loyalty Engine доступен?) then (Да)
  :Рассчитать баллы;
  :Начислить баллы клиенту;
  :Отправить push-уведомление;
else (Нет)
  :Сохранить транзакцию в очередь;
  :Сообщить клиенту об ожидании;
endif
:Обновить баланс и историю в приложении;
stop
@enduml
"""
        
        print("\n🧪 Тест сложной диаграммы с кириллицей:")
        print(f"   Код: {len(plantuml_code.strip())} символов")
        
        # Test UTF-8 encoding
        url1, success1 = test_plantuml_encoding(plantuml_code)
        print(f"   UTF-8 метод: {'✅ Работает' if success1 else '❌ Не работает'}")
        print(f"   URL: {url1[:80]}...")
        
        # Test DEFLATE encoding
        url2, success2 = test_plantuml_defalte_encoding(plantuml_code)
        print(f"   DEFLATE метод: {'✅ Работает' if success2 else '❌ Не работает'}")
        print(f"   URL: {url2[:80]}...")
        
        assert success1 or success2, "Хотя бы один метод кодирования должен работать"
        return url1 if success1 else url2
    
    def test_sequence_diagram(self):
        """Test PlantUML sequence diagram."""
        plantuml_code = """
@startuml
participant "HR-администратор" as HR
participant "Пользователь" as User
participant "Инструктор" as Instructor
participant "Система" as System

HR -> Instructor: Создать курс
Instructor -> System: Добавить контент курса
System -> User: Назначить курс пользователю
User -> System: Пройти курс
System -> User: Выдать сертификат
@enduml
"""
        
        print("\n🧪 Тест диаграммы последовательности:")
        print(f"   Код: {len(plantuml_code.strip())} символов")
        
        # Test UTF-8 encoding
        url1, success1 = test_plantuml_encoding(plantuml_code)
        print(f"   UTF-8 метод: {'✅ Работает' if success1 else '❌ Не работает'}")
        print(f"   URL: {url1[:80]}...")
        
        assert success1, "UTF-8 кодирование должно работать для диаграммы последовательности"
        return url1


if __name__ == "__main__":
    # Run tests manually
    test = TestPlantUMLVisualization()
    
    print("=" * 60)
    print("🧪 Тестирование PlantUML визуализации")
    print("=" * 60)
    
    print("\n1. Тест простой диаграммы:")
    url1 = test.test_simple_diagram()
    
    print("\n2. Тест сложной диаграммы с кириллицей:")
    url2 = test.test_complex_diagram_with_cyrillic()
    
    print("\n3. Тест диаграммы последовательности:")
    url3 = test.test_sequence_diagram()
    
    print("\n" + "=" * 60)
    print("✅ Все тесты пройдены!")
    print("=" * 60)
    print(f"\n💡 Откройте эти URL в браузере для визуальной проверки:")
    print(f"   1. Простая диаграмма: {url1}")
    print(f"   2. Сложная диаграмма: {url2}")
    print(f"   3. Диаграмма последовательности: {url3}")

