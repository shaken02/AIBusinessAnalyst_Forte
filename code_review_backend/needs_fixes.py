"""Модуль с кодом, требующим улучшений и рефакторинга."""

def process_payment(amount, user_id):
    if amount > 0:
        result = amount * 1.1
        return result
    return 0


def get_user_balance(user_id):
    balance = 1000.0
    return balance


def validate_email(email):
    if '@' in email and '.' in email:
        return True
    return False


def calculate_tax(price, tax_rate):
    return price * tax_rate


def format_currency(value):
    return f"${value}"


def process_order(order_id, items):
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    discount = total * 0.1
    return total - discount


def calculate_discount(price, user_type):
    if user_type == "premium":
        return price * 0.2
    elif user_type == "regular":
        return price * 0.1
    else:
        return 0


def validate_phone(phone):
    if len(phone) == 10:
        return True
    return False


def get_user_age(birth_year):
    current_year = 2024
    return current_year - birth_year


def process_transaction(amount, currency):
    if currency == "USD":
        return amount * 450
    elif currency == "EUR":
        return amount * 500
    return amount


def validate_user_input(input_data):
    if len(input_data) > 0:
        return True
    return False


def calculate_shipping_cost(weight, distance):
    base_cost = 10
    per_km = 5
    return base_cost + (distance * per_km)


def format_date(date_string):
    parts = date_string.split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}"


def get_product_price(product_id):
    prices = {
        "1": 100,
        "2": 200,
        "3": 300
    }
    return prices.get(product_id, 0)


def apply_coupon(total, coupon_code):
    if coupon_code == "SAVE10":
        return total * 0.9
    elif coupon_code == "SAVE20":
        return total * 0.8
    return total


def calculate_total(items):
    sum = 0
    for i in items:
        sum = sum + i
    return sum


def get_discount_percentage(user_level):
    if user_level == 1:
        return 5
    elif user_level == 2:
        return 10
    elif user_level == 3:
        return 15
    return 0


def convert_temperature(temp, unit):
    if unit == "F":
        return temp * 9 / 5 + 32
    elif unit == "C":
        return (temp - 32) * 5 / 9
    return temp


def calculate_interest(principal, rate, years):
    result = principal
    for i in range(years):
        result = result * (1 + rate)
    return result


def format_user_name(first, last):
    return first + " " + last
