"""Модуль с примерами плохого кода с критическими проблемами."""

import os

# КРИТИЧЕСКАЯ ПРОБЛЕМА: жестко закодированные секреты
DATABASE_PASSWORD = "admin12345"
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "my_secret_token_2024"

def authenticate_user(username, password):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: SQL injection уязвимость
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: логирование пароля в открытом виде
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
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сравнение токенов через == (timing attack)
    if token == SECRET_TOKEN:
        return True
    return False


def store_user_password(user_id, password):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сохранение пароля в открытом виде без хеширования
    file_path = f"/tmp/user_{user_id}_password.txt"
    with open(file_path, "w") as f:
        f.write(f"User {user_id} password: {password}")
    print(f"Stored password for user {user_id}: {password}")
    return True


def render_user_content(user_input):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: XSS уязвимость - нет экранирования
    html_content = f"<div>{user_input}</div>"
    return html_content


def execute_user_code(code_string):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: выполнение произвольного кода (RCE)
    result = eval(code_string)
    return result


def download_file_from_url(url, save_path):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки URL на SSRF
    import urllib.request
    urllib.request.urlretrieve(url, save_path)
    return True


def process_payment(card_number, cvv, amount):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: логирование данных карты
    print(f"Processing payment: card={card_number}, cvv={cvv}, amount={amount}")
    return {"status": "success", "card_last4": card_number[-4:]}


def upload_file(file_path, user_id):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: Path Traversal уязвимость
    upload_dir = f"/uploads/{user_id}/{file_path}"
    with open(upload_dir, "wb") as f:
        f.write(b"file content")
    return True


def deserialize_data(data_string):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: небезопасная десериализация (pickle RCE)
    import pickle
    data = pickle.loads(data_string.encode())
    return data


def delete_user_data(user_id):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: использование os.system с пользовательским вводом
    os.system(f"rm -rf /data/users/{user_id}/*")
    return True


def reset_user_password(email):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки существования пользователя
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: утечка информации (можно узнать, зарегистрирован ли email)
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: генерация слабого пароля
    new_password = "123456"  # Слабый пароль
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: отправка пароля в открытом виде
    print(f"New password for {email}: {new_password}")
    return True


def generate_api_key(user_id):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: использование небезопасного генератора случайных чисел
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: слабый алгоритм генерации ключа
    import random
    api_key = str(random.randint(100000, 999999))
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: сохранение ключа в открытом виде
    with open(f"/tmp/api_key_{user_id}.txt", "w") as f:
        f.write(api_key)
    return api_key


def check_permissions(user_id, resource_id):
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: нет проверки прав доступа
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: любой пользователь может получить доступ к любому ресурсу
    # КРИТИЧЕСКАЯ ПРОБЛЕМА: отсутствие авторизации
    return True  # Всегда разрешает доступ
