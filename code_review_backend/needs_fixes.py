"""Модуль с кодом, требующим улучшений."""

def process_payment(amount, user_id):
    # Проблема: нет type hints
    # Проблема: нет docstring
    # Проблема: нет проверки на отрицательные значения
    if amount > 0:
        result = amount * 1.1  # Непонятно что это за коэффициент
        return result
    return 0


def get_user_balance(user_id):
    # Проблема: нет обработки ошибок
    # Проблема: нет type hints
    # Проблема: жестко закодированное значение
    balance = 1000.0
    return balance


def validate_email(email):
    # Проблема: примитивная проверка email
    # Проблема: нет использования стандартных библиотек
    if '@' in email and '.' in email:
        return True
    return False


def calculate_tax(price, tax_rate):
    # Новая функция с проблемами
    # Проблема: нет проверки на None
    # Проблема: нет type hints
    # Проблема: может вернуть отрицательное значение
    return price * tax_rate


def format_currency(value):
    # Новая функция с проблемами
    # Проблема: нет обработки ошибок
    # Проблема: нет проверки типа
    return f"${value}"


def process_order(order_id, items):
    # Новая функция с проблемами стиля
    # Проблема: нет type hints
    # Проблема: нет docstring
    # Проблема: магические числа
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    # Проблема: жестко закодированная скидка
    discount = total * 0.1
    return total - discount


def calculate_discount(price, user_type):
    # Проблема: нет type hints
    # Проблема: нет docstring
    # Проблема: магические числа в условиях
    if user_type == "premium":
        return price * 0.2
    elif user_type == "regular":
        return price * 0.1
    else:
        return 0


def validate_phone(phone):
    # Проблема: примитивная валидация
    # Проблема: нет использования регулярных выражений
    # Проблема: нет проверки формата
    if len(phone) == 10:
        return True
    return False


def get_user_age(birth_year):
    # Проблема: нет проверки на None
    # Проблема: нет type hints
    # Проблема: жестко закодированный текущий год
    current_year = 2024
    return current_year - birth_year

