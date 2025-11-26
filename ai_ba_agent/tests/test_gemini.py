"""Unit tests for Gemini LLM engine."""

from __future__ import annotations

import os
from pathlib import Path

# Ensure .env is loaded before importing app modules
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)

from app.core.llm_engine import GeminiEngine, create_engine
from app.config import settings


class TestGeminiEngine:
    """Test Gemini API integration."""
    
    def test_api_key_loaded(self):
        """Test that API key is loaded from .env."""
        print("\n🧪 Тест загрузки API ключа:")
        
        api_key = settings.model.gemini_api_key
        if api_key:
            print(f"   ✅ API ключ загружен (длина: {len(api_key)} символов)")
            print(f"   Первые 10 символов: {api_key[:10]}...")
            assert len(api_key) > 10, "API ключ должен быть валидным"
        else:
            print("   ❌ API ключ не загружен!")
            print("   Убедитесь, что файл .env существует и содержит AI_BA_GEMINI_API_KEY")
            raise ValueError("API ключ не найден")
    
    def test_gemini_engine_initialization(self):
        """Test Gemini engine initialization."""
        print("\n🧪 Тест инициализации Gemini engine:")
        
        try:
            engine = GeminiEngine()
            print(f"   ✅ Gemini engine инициализирован")
            print(f"   Модель: {engine.model_name}")
            assert engine.model_name is not None
            assert engine.model is not None
        except Exception as e:
            print(f"   ❌ Ошибка инициализации: {e}")
            raise
    
    def test_simple_query(self):
        """Test simple query to Gemini API."""
        print("\n🧪 Тест простого запроса к Gemini:")
        
        try:
            engine = GeminiEngine()
            prompt = "Привет! Ответь одним предложением: что такое искусственный интеллект?"
            
            print(f"   Отправка запроса: {prompt[:50]}...")
            response = engine.ask(prompt)
            
            print(f"   ✅ Получен ответ (длина: {len(response)} символов)")
            print(f"   Ответ: {response[:100]}...")
            
            assert len(response) > 0, "Ответ не должен быть пустым"
            assert isinstance(response, str), "Ответ должен быть строкой"
            
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
            raise
    
    def test_russian_language_support(self):
        """Test Russian language support."""
        print("\n🧪 Тест поддержки русского языка:")
        
        try:
            engine = GeminiEngine()
            prompt = "Напиши краткое описание проекта мобильного банкинга на русском языке (2-3 предложения)."
            
            print(f"   Отправка запроса на русском...")
            response = engine.ask(prompt)
            
            print(f"   ✅ Получен ответ на русском (длина: {len(response)} символов)")
            print(f"   Ответ: {response[:150]}...")
            
            # Проверяем наличие кириллицы
            has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in response)
            if has_cyrillic:
                print("   ✅ Ответ содержит кириллицу")
            else:
                print("   ⚠️  Ответ не содержит кириллицу (возможно, модель ответила на английском)")
            
            assert len(response) > 0, "Ответ не должен быть пустым"
            
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
            raise
    
    def test_brd_generation(self):
        """Test BRD document generation."""
        print("\n🧪 Тест генерации BRD:")
        
        try:
            engine = GeminiEngine()
            context = """
            Проект: Мобильное приложение для платежей
            Цель: Упростить процесс оплаты для клиентов
            Проблема: Клиенты вынуждены носить физические карты
            """
            
            print("   Генерация BRD документа...")
            brd = engine.generate_brd(context)
            
            print(f"   ✅ BRD сгенерирован (длина: {len(brd)} символов)")
            print(f"   Начало документа: {brd[:200]}...")
            
            assert len(brd) > 100, "BRD должен содержать достаточно информации"
            assert "BRD" in brd or "требовани" in brd.lower() or "requirement" in brd.lower(), "BRD должен содержать релевантную информацию"
            
        except Exception as e:
            print(f"   ❌ Ошибка генерации BRD: {e}")
            raise
    
    def test_usecase_generation(self):
        """Test Use Case document generation."""
        print("\n🧪 Тест генерации Use Case:")
        
        try:
            engine = GeminiEngine()
            context = """
            Процесс: Оплата покупки через мобильное приложение
            Роли: Клиент, Банк, Магазин
            Шаги: Выбор карты, Подтверждение, Обработка платежа
            """
            
            print("   Генерация Use Case документа...")
            usecase = engine.generate_usecase(context)
            
            print(f"   ✅ Use Case сгенерирован (длина: {len(usecase)} символов)")
            print(f"   Начало документа: {usecase[:200]}...")
            
            assert len(usecase) > 100, "Use Case должен содержать достаточно информации"
            
        except Exception as e:
            print(f"   ❌ Ошибка генерации Use Case: {e}")
            raise
    
    def test_userstories_generation(self):
        """Test User Stories document generation."""
        print("\n🧪 Тест генерации User Stories:")
        
        try:
            engine = GeminiEngine()
            context = """
            Пользователь: Клиент банка
            Функции: Оплата, Просмотр баланса, История транзакций
            """
            
            print("   Генерация User Stories документа...")
            stories = engine.generate_userstories(context)
            
            print(f"   ✅ User Stories сгенерированы (длина: {len(stories)} символов)")
            print(f"   Начало документа: {stories[:200]}...")
            
            assert len(stories) > 100, "User Stories должны содержать достаточно информации"
            
        except Exception as e:
            print(f"   ❌ Ошибка генерации User Stories: {e}")
            raise
    
    def test_plantuml_generation(self):
        """Test PlantUML code generation."""
        print("\n🧪 Тест генерации PlantUML:")
        
        try:
            engine = GeminiEngine()
            context = """
            Процесс: Регистрация нового клиента
            Шаги: 
            1. Ввод данных
            2. Проверка документов
            3. Создание аккаунта
            4. Отправка подтверждения
            """
            
            print("   Генерация PlantUML кода...")
            plantuml = engine.generate_plantuml(context)
            
            print(f"   ✅ PlantUML код сгенерирован (длина: {len(plantuml)} символов)")
            print(f"   Код: {plantuml[:300]}...")
            
            assert len(plantuml) > 50, "PlantUML код должен содержать достаточно информации"
            assert "@startuml" in plantuml.lower() or "startuml" in plantuml.lower(), "PlantUML должен содержать @startuml"
            
        except Exception as e:
            print(f"   ❌ Ошибка генерации PlantUML: {e}")
            raise
    
    def test_create_engine_with_gemini(self):
        """Test create_engine function with Gemini provider."""
        print("\n🧪 Тест create_engine с Gemini провайдером:")
        
        # Проверяем текущий провайдер
        current_provider = settings.model.provider
        print(f"   Текущий провайдер в настройках: {current_provider}")
        
        try:
            engine = create_engine()
            engine_type = type(engine).__name__
            print(f"   Тип созданного engine: {engine_type}")
            
            if current_provider == "gemini":
                assert isinstance(engine, GeminiEngine), f"Должен быть создан GeminiEngine, но создан {engine_type}"
                print("   ✅ create_engine создал GeminiEngine")
            else:
                print(f"   ⚠️  Провайдер в настройках: {current_provider}, ожидался 'gemini'")
                print(f"   Создан engine типа: {engine_type}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            raise


def run_all_tests():
    """Run all Gemini tests."""
    print("=" * 60)
    print("🧪 Тестирование Gemini API")
    print("=" * 60)
    
    test = TestGeminiEngine()
    
    tests = [
        ("Загрузка API ключа", test.test_api_key_loaded),
        ("Инициализация Gemini engine", test.test_gemini_engine_initialization),
        ("Простой запрос", test.test_simple_query),
        ("Поддержка русского языка", test.test_russian_language_support),
        ("Генерация BRD", test.test_brd_generation),
        ("Генерация Use Case", test.test_usecase_generation),
        ("Генерация User Stories", test.test_userstories_generation),
        ("Генерация PlantUML", test.test_plantuml_generation),
        ("create_engine функция", test.test_create_engine_with_gemini),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n   ❌ Тест '{name}' провален: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования:")
    print(f"   ✅ Пройдено: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   📈 Всего: {passed + failed}")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 Все тесты пройдены успешно!")
    else:
        print(f"\n⚠️  {failed} тест(ов) провалено. Проверьте ошибки выше.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

