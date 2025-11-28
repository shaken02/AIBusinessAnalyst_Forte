"""Модуль с примерами плохого кода с критическими проблемами."""

import os

DATABASE_PASSWORD = "admin12345"
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "my_secret_token_2024"

def authenticate_user(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    print(f"User {username} logged in with password: {password}")
    return True


def process_sensitive_data(data):
    file_path = "/tmp/sensitive_data.txt"
    with open(file_path, "w") as f:
        f.write(str(data))
    print(f"Sensitive data processed: {data}")


def get_admin_credentials():
    return {
        "username": "admin",
        "password": "super_secret_password_123"
    }


def validate_api_request(token):
    if token == SECRET_TOKEN:
        return True
    return False


def store_user_password(user_id, password):
    file_path = f"/tmp/user_{user_id}_password.txt"
    with open(file_path, "w") as f:
        f.write(f"User {user_id} password: {password}")
    print(f"Stored password for user {user_id}: {password}")
    return True


def render_user_content(user_input):
    html_content = f"<div>{user_input}</div>"
    return html_content


def execute_user_code(code_string):
    result = eval(code_string)
    return result


def download_file_from_url(url, save_path):
    import urllib.request
    urllib.request.urlretrieve(url, save_path)
    return True


def process_payment(card_number, cvv, amount):
    print(f"Processing payment: card={card_number}, cvv={cvv}, amount={amount}")
    return {"status": "success", "card_last4": card_number[-4:]}


def upload_file(file_path, user_id):
    upload_dir = f"/uploads/{user_id}/{file_path}"
    with open(upload_dir, "wb") as f:
        f.write(b"file content")
    return True


def deserialize_data(data_string):
    import pickle
    data = pickle.loads(data_string.encode())
    return data


def delete_user_data(user_id):
    os.system(f"rm -rf /data/users/{user_id}/*")
    return True


def reset_user_password(email):
    new_password = "123456"
    print(f"New password for {email}: {new_password}")
    return True


def generate_api_key(user_id):
    import random
    api_key = str(random.randint(100000, 999999))
    with open(f"/tmp/api_key_{user_id}.txt", "w") as f:
        f.write(api_key)
    return api_key


def check_permissions(user_id, resource_id):
    return True


def update_user_profile(user_id, new_data):
    query = f"UPDATE users SET {new_data} WHERE id={user_id}"
    print(f"Executing query: {query}")
    return True


def get_user_session(session_id):
    session_file = f"/tmp/session_{session_id}.txt"
    with open(session_file, "r") as f:
        return f.read()


def save_credit_card(user_id, card_number, expiry, cvv):
    card_data = f"{user_id}:{card_number}:{expiry}:{cvv}"
    with open(f"/tmp/cards_{user_id}.txt", "a") as f:
        f.write(card_data + "\n")
    print(f"Saved card for user {user_id}: {card_number}")


def run_database_query(query_string):
    import subprocess
    result = subprocess.run(f"mysql -u root -p{DATABASE_PASSWORD} -e '{query_string}'", shell=True, capture_output=True)
    return result.stdout.decode()


def backup_database():
    backup_cmd = f"mysqldump -u root -p{DATABASE_PASSWORD} --all-databases > /tmp/backup.sql"
    os.system(backup_cmd)
    print(f"Database backed up using password: {DATABASE_PASSWORD}")
    return True


def send_email_with_credentials(to_email, subject, body):
    smtp_password = "email_password_123"
    print(f"Sending email to {to_email} with password: {smtp_password}")
    return True
