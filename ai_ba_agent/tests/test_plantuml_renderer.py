"""Unit tests for PlantUML local renderer."""

from __future__ import annotations

import os
from pathlib import Path

from app.utils.plantuml_renderer import render_plantuml_to_png


class TestPlantUMLLocalRenderer:
    """Test local PlantUML rendering via Java."""
    
    def __init__(self, output_dir: str = "test_data_output"):
        """Initialize test with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        print(f"\n📁 Тестовые диаграммы будут сохранены в: {self.output_dir.absolute()}")
    
    def test_simple_activity_diagram(self):
        """Test simple activity diagram rendering."""
        plantuml_code = """
@startuml
start
:Регистрация клиента;
:Начисление баллов;
stop
@enduml
"""
        
        print("\n🧪 Тест 1: Простая activity диаграмма")
        png_bytes = render_plantuml_to_png(plantuml_code)
        
        if png_bytes:
            output_path = self.output_dir / "test_01_simple_activity.png"
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            print(f"   ✅ Диаграмма сохранена: {output_path}")
            print(f"   Размер: {len(png_bytes)} байт ({len(png_bytes) / 1024:.2f} KB)")
            return True
        else:
            print(f"   ❌ Не удалось сгенерировать диаграмму")
            return False
    
    def test_complex_diagram_with_cyrillic(self):
        """Test complex diagram with Cyrillic text."""
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
        
        print("\n🧪 Тест 2: Сложная диаграмма с кириллицей")
        png_bytes = render_plantuml_to_png(plantuml_code)
        
        if png_bytes:
            output_path = self.output_dir / "test_02_complex_cyrillic.png"
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            print(f"   ✅ Диаграмма сохранена: {output_path}")
            print(f"   Размер: {len(png_bytes)} байт ({len(png_bytes) / 1024:.2f} KB)")
            return True
        else:
            print(f"   ❌ Не удалось сгенерировать диаграмму")
            return False
    
    def test_sequence_diagram(self):
        """Test sequence diagram."""
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
        
        print("\n🧪 Тест 3: Диаграмма последовательности")
        png_bytes = render_plantuml_to_png(plantuml_code)
        
        if png_bytes:
            output_path = self.output_dir / "test_03_sequence_diagram.png"
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            print(f"   ✅ Диаграмма сохранена: {output_path}")
            print(f"   Размер: {len(png_bytes)} байт ({len(png_bytes) / 1024:.2f} KB)")
            return True
        else:
            print(f"   ❌ Не удалось сгенерировать диаграмму")
            return False
    
    def test_real_world_scenario(self):
        """Test real-world scenario from the application."""
        plantuml_code = """
@startuml
title Процесс онлайн-обучения для корпоративных клиентов

participant "HR-администратор" as HR
participant "Сотрудник" as User
participant "Администратор курсов" as Admin
participant "Мобильное приложение" as App

note right of HR: Создание и назначение курса
HR -> App: Создать курс
HR -> App: Назначить курс сотрудникам
note left of User: Получение уведомления о новом курсе
App --> User: Уведомление о новом курсе
note right of User: Просмотр видеолекций и прохождение тестов
User -> App: Открыть мобильное приложение
User -> App: Просмотреть видеолекции
User -> App: Пройти тесты после каждого модуля
note left of Admin: Отрывки о прохождении курсов и назначение дополнительных курсов
App --> Admin: Отчеты о прохождении курсов
Admin -> App: Назначить дополнительные курсы
note right of App: Автоматическое выдача сертификата при успешном завершении
App --> User: Сертификат
@enduml
"""
        
        print("\n🧪 Тест 4: Реальный сценарий из приложения")
        png_bytes = render_plantuml_to_png(plantuml_code)
        
        if png_bytes:
            output_path = self.output_dir / "test_04_real_world_scenario.png"
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            print(f"   ✅ Диаграмма сохранена: {output_path}")
            print(f"   Размер: {len(png_bytes)} байт ({len(png_bytes) / 1024:.2f} KB)")
            return True
        else:
            print(f"   ❌ Не удалось сгенерировать диаграмму")
            return False
    
    def test_without_tags(self):
        """Test PlantUML code without @startuml/@enduml tags."""
        plantuml_code = """
start
:Тест без тегов;
stop
"""
        
        print("\n🧪 Тест 5: Код без @startuml/@enduml тегов")
        png_bytes = render_plantuml_to_png(plantuml_code)
        
        if png_bytes:
            output_path = self.output_dir / "test_05_without_tags.png"
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            print(f"   ✅ Диаграмма сохранена: {output_path}")
            print(f"   Размер: {len(png_bytes)} байт ({len(png_bytes) / 1024:.2f} KB)")
            return True
        else:
            print(f"   ❌ Не удалось сгенерировать диаграмму")
            return False
    
    def run_all_tests(self):
        """Run all tests and return summary."""
        print("=" * 60)
        print("🧪 ТЕСТИРОВАНИЕ ЛОКАЛЬНОГО РЕНДЕРИНГА PLANTUML")
        print("=" * 60)
        
        results = []
        
        results.append(("Простая activity диаграмма", self.test_simple_activity_diagram()))
        results.append(("Сложная диаграмма с кириллицей", self.test_complex_diagram_with_cyrillic()))
        results.append(("Диаграмма последовательности", self.test_sequence_diagram()))
        results.append(("Реальный сценарий", self.test_real_world_scenario()))
        results.append(("Код без тегов", self.test_without_tags()))
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {name}")
        
        print(f"\n✅ Успешно: {passed}/{total}")
        print(f"❌ Провалено: {total - passed}/{total}")
        
        print(f"\n💡 Откройте папку для визуальной проверки:")
        print(f"   {self.output_dir.absolute()}")
        print(f"   open {self.output_dir.absolute()}")
        
        return passed == total


if __name__ == "__main__":
    # Run tests
    test = TestPlantUMLLocalRenderer()
    success = test.run_all_tests()
    
    if success:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Проверьте логи выше.")
    
    exit(0 if success else 1)

