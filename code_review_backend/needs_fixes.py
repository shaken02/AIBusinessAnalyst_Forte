"""Модуль с кодом, требующим улучшений и рефакторинга."""

def process_payment(amount, user_id):
    # Проблема: нет type hints
    # Проблема: нет docstring
    # Проблема: нет проверки на отрицательные значения
    if amount > 0:
        result = amount * 1.1  # Непонятно что это за коэффициент (комиссия?)
        return result
    return 0


def get_user_balance(user_id):
    # Проблема: нет обработки ошибок
    # Проблема: нет type hints
    # Проблема: жестко закодированное значение вместо обращения к БД
    balance = 1000.0
    return balance


def validate_email(email):
    # Проблема: примитивная проверка email
    # Проблема: нет использования регулярных выражений или библиотек
    # Проблема: может пропустить невалидные email
    if '@' in email and '.' in email:
        return True
    return False


def calculate_tax(price, tax_rate):
    # Проблема: нет проверки на None
    # Проблема: нет type hints
    # Проблема: может вернуть отрицательное значение
    # Проблема: нет проверки диапазона tax_rate
    return price * tax_rate


def format_currency(value):
    # Проблема: нет обработки ошибок
    # Проблема: нет проверки типа
    # Проблема: жестко закодированная валюта
    return f"${value}"


def process_order(order_id, items):
    # Проблема: нет type hints
    # Проблема: нет docstring
    # Проблема: магические числа (0.1 - это скидка?)
    # Проблема: нет обработки пустого списка items
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    discount = total * 0.1  # Жестко закодированная скидка 10%
    return total - discount


def calculate_discount(price, user_type):
    # Проблема: нет type hints
    # Проблема: нет docstring
    # Проблема: магические числа в условиях (0.2, 0.1)
    # Проблема: нет обработки неизвестного user_type
    if user_type == "premium":
        return price * 0.2
    elif user_type == "regular":
        return price * 0.1
    else:
        return 0


def validate_phone(phone):
    # Проблема: примитивная валидация
    # Проблема: нет использования регулярных выражений
    # Проблема: проверяет только длину, не формат
    if len(phone) == 10:
        return True
    return False


def get_user_age(birth_year):
    # Проблема: нет проверки на None
    # Проблема: нет type hints
    # Проблема: жестко закодированный текущий год (будет неверным в следующем году)
    current_year = 2024
    return current_year - birth_year


def process_transaction(amount, currency):
    # Проблема: нет проверки на отрицательные значения
    # Проблема: нет валидации валюты
    # Проблема: нет обработки ошибок
    # Проблема: жестко закодированные курсы валют (должны быть из API)
    if currency == "USD":
        return amount * 450  # Жестко закодированный курс
    elif currency == "EUR":
        return amount * 500
    return amount


def validate_user_input(input_data):
    # Проблема: нет проверки типа данных
    # Проблема: нет санитизации входных данных
    # Проблема: примитивная валидация (только проверка длины)
    if len(input_data) > 0:
        return True
    return False
