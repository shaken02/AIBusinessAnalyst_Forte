"""Модуль с критическими проблемами безопасности."""

import os

# КРИТИЧЕСКАЯ ПРОБЛЕМА: жестко закодированный пароль
DATABASE_PASSWORD = "admin12345"

# КРИТИЧЕСКАЯ ПРОБЛЕМА: API ключ в коде
API_KEY = "sk-1234567890abcdef"

# КРИТИЧЕСКАЯ ПРОБЛЕМА: новый секретный токен в коде
SECRET_TOKEN = "my_secret_token_2024"

def authenticate_user(username, password):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: SQL injection уязвимость
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # Выполнение запроса без параметризации
    
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: логирование пароля
    print(f"User {username} logged in with password: {password}")
    
    return True


def process_sensitive_data(data):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки входных данных
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сохранение в небезопасное место
    file_path = "/tmp/sensitive_data.txt"
    with open(file_path, "w") as f:
        f.write(str(data))
    
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: передача секретных данных в логи
    print(f"Sensitive data processed: {data}")


def get_admin_credentials():
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: возврат секретных данных
    return {
        "username": "admin",
        "password": "super_secret_password_123"
    }


def validate_api_request(token):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сравнение токенов через == вместо безопасного сравнения
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет защиты от timing attacks
    if token == SECRET_TOKEN:
        return True
    return False


def store_user_password(user_id, password):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сохранение пароля в открытом виде
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет хеширования
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сохранение в небезопасное место
    file_path = f"/tmp/user_{user_id}_password.txt"
    with open(file_path, "w") as f:
        f.write(f"User {user_id} password: {password}")
    
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: логирование пароля
    print(f"Stored password for user {user_id}: {password}")
    return True

