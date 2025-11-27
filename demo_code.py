"""
Демонстрационный файл для проверки AI Code Review.
Содержит правильный и неправильный код.
"""

# ✅ ПРАВИЛЬНЫЙ КОД: Хорошая функция с обработкой ошибок
def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Вычисляет цену со скидкой.
    
    Args:
        price: Исходная цена
        discount_percent: Процент скидки (0-100)
    
    Returns:
        Цена со скидкой
    
    Raises:
        ValueError: Если цена или скидка отрицательные
    """
    if price < 0:
        raise ValueError("Цена не может быть отрицательной")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Скидка должна быть от 0 до 100%")
    
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount


# ❌ НЕПРАВИЛЬНЫЙ КОД: Плохая функция без проверок и с багом
def divide_numbers(a, b):
    # Проблема 1: Нет проверки на деление на ноль
    # Проблема 2: Нет типизации
    # Проблема 3: Нет документации
    # Проблема 4: Потенциальный баг - не обрабатывает отрицательные числа правильно
    result = a / b
    return result


# ❌ НЕПРАВИЛЬНЫЙ КОД: Утечка данных, нет валидации
def process_user_data(username, password):
    # Проблема 1: Пароль передается в открытом виде (без хеширования)
    # Проблема 2: Нет валидации входных данных
    # Проблема 3: Логирование пароля в открытом виде (проблема безопасности)
    print(f"Processing user: {username} with password: {password}")
    return {"username": username, "password": password}


# ✅ ПРАВИЛЬНЫЙ КОД: Безопасная обработка данных
def process_user_data_safe(username: str, password_hash: str) -> dict:
    """
    Безопасная обработка данных пользователя.
    
    Args:
        username: Имя пользователя
        password_hash: Хеш пароля (не оригинальный пароль!)
    
    Returns:
        Словарь с данными пользователя
    """
    if not username or len(username) < 3:
        raise ValueError("Имя пользователя должно быть минимум 3 символа")
    if not password_hash:
        raise ValueError("Хеш пароля обязателен")
    
    # Никогда не логируем пароль или его хеш
    return {"username": username, "authenticated": True}

