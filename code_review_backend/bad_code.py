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


def render_user_content(user_input):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: XSS уязвимость - нет экранирования пользовательского ввода
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: прямой вывод без санитизации
    html_content = f"<div>{user_input}</div>"
    return html_content


def decrypt_data(encrypted_data):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: жестко закодированный ключ шифрования
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: ключ должен быть в переменных окружения
    encryption_key = "hardcoded_secret_key_12345"
    
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: использование небезопасного алгоритма шифрования
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки целостности данных
    decrypted = encrypted_data  # Упрощенная логика для примера
    return decrypted


def execute_user_code(code_string):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: выполнение произвольного кода пользователя
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет валидации входных данных
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: может привести к RCE (Remote Code Execution)
    result = eval(code_string)
    return result


def download_file_from_url(url, save_path):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки URL на SSRF (Server-Side Request Forgery)
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: может быть использовано для атаки на внутренние сервисы
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет валидации пути сохранения
    import urllib.request
    urllib.request.urlretrieve(url, save_path)
    return True


def set_user_session(user_id, session_data):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки прав доступа
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: любой пользователь может изменить сессию другого
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет валидации session_data
    session_file = f"/tmp/session_{user_id}.json"
    import json
    with open(session_file, "w") as f:
        json.dump(session_data, f)
    return True


def delete_user_data(user_id):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки прав доступа
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет подтверждения удаления
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: использование os.system с пользовательским вводом
    import os
    os.system(f"rm -rf /data/users/{user_id}/*")
    return True


def process_payment(card_number, cvv, amount):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: логирование данных карты
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет шифрования чувствительных данных
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: передача CVV в открытом виде
    print(f"Processing payment: card={card_number}, cvv={cvv}, amount={amount}")
    # Обработка платежа без шифрования
    return {"status": "success", "card_last4": card_number[-4:]}


def upload_file(file_path, user_id):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки типа файла
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки размера файла
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: путь формируется из пользовательского ввода (Path Traversal)
    upload_dir = f"/uploads/{user_id}/{file_path}"
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет санитизации пути
    with open(upload_dir, "wb") as f:
        f.write(b"file content")  # Упрощенная логика
    return True


def reset_password(email):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки существования пользователя
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: утечка информации (можно узнать, зарегистрирован ли email)
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: генерация слабого пароля
    new_password = "123456"  # Слабый пароль
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: отправка пароля в открытом виде
    print(f"New password for {email}: {new_password}")
    return True

