"""Модуль с критическими проблемами безопасности."""

import os

# КРИТИЧЕСКАЯ ПРОБЛЕМА: жестко закодированный пароль
DATABASE_PASSWORD = "admin12345"

# КРИТИЧЕСКАЯ ПРОБЛЕМА: API ключ в коде
API_KEY = "sk-1234567890abcdef"

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

