"""Модуль с примерами качественного кода, следующий лучшим практикам."""

from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Роли пользователей в системе."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass
class User:
    """Модель пользователя."""
    user_id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime


def calculate_total_price(items: List[Dict[str, Any]], discount: Optional[float] = None) -> float:
    """
    Рассчитывает общую стоимость товаров с учетом скидки.
    
    Args:
        items: Список товаров с обязательными полями 'price' и 'quantity'
        discount: Процент скидки (от 0 до 100), опционально
        
    Returns:
        Общая стоимость после применения скидки, округленная до 2 знаков
        
    Raises:
        ValueError: Если цена или количество отрицательные, или скидка вне диапазона
        KeyError: Если отсутствуют обязательные поля 'price' или 'quantity'
    """
    if not items:
        logger.warning("Empty items list provided")
        return 0.0
    
    total = 0.0
    for idx, item in enumerate(items):
        try:
            price = float(item['price'])
            quantity = int(item['quantity'])
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Invalid item at index {idx}: {e}")
            raise ValueError(f"Item at index {idx} must have valid 'price' and 'quantity' fields")
        
        if price < 0 or quantity < 0:
            raise ValueError(f"Price and quantity must be non-negative (item at index {idx})")
        
        total += price * quantity
    
    if discount is not None:
        if not 0 <= discount <= 100:
            raise ValueError("Discount must be between 0 and 100 percent")
        total = total * (1 - discount / 100)
        logger.info(f"Applied discount: {discount}%")
    
    return round(total, 2)


def format_user_data(user: User) -> Dict[str, Any]:
    """
    Форматирует данные пользователя для безопасного логирования.
    
    Args:
        user: Объект пользователя
        
    Returns:
        Словарь с отформатированными данными (без чувствительной информации)
    """
    logger.info(f"Formatting user data for user_id: {user.user_id}")
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "formatted_at": datetime.now().isoformat(),
        "status": "active"
    }


def validate_email(email: str) -> bool:
    """
    Валидирует email адрес.
    
    Args:
        email: Email адрес для проверки
        
    Returns:
        True если email валиден, False в противном случае
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def process_payment(amount: float, currency: str, user_id: str) -> Dict[str, Any]:
    """
    Обрабатывает платеж пользователя.
    
    Args:
        amount: Сумма платежа (должна быть положительной)
        currency: Валюта платежа (USD, EUR, KZT)
        user_id: Идентификатор пользователя
        
    Returns:
        Словарь с результатом обработки платежа
        
    Raises:
        ValueError: Если сумма отрицательная или валюта не поддерживается
    """
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    
    supported_currencies = {"USD", "EUR", "KZT"}
    if currency not in supported_currencies:
        raise ValueError(f"Unsupported currency: {currency}. Supported: {supported_currencies}")
    
    logger.info(f"Processing payment: {amount} {currency} for user {user_id}")
    
    transaction_id = f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:8]}"
    
    return {
        "status": "success",
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "processed_at": datetime.now().isoformat()
    }


def calculate_discount(price: float, user_role: UserRole) -> float:
    """
    Рассчитывает скидку в зависимости от роли пользователя.
    
    Args:
        price: Исходная цена
        user_role: Роль пользователя
        
    Returns:
        Размер скидки в денежных единицах
    """
    DISCOUNT_RATES = {
        UserRole.ADMIN: 0.25,
        UserRole.USER: 0.10,
        UserRole.GUEST: 0.0
    }
    
    discount_rate = DISCOUNT_RATES.get(user_role, 0.0)
    return round(price * discount_rate, 2)


def get_user_statistics(user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
    Получает статистику пользователя за указанный период.
    
    Args:
        user_id: Идентификатор пользователя
        start_date: Начальная дата периода
        end_date: Конечная дата периода
        
    Returns:
        Словарь со статистикой пользователя
        
    Raises:
        ValueError: Если start_date позже end_date
    """
    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date")
    
    logger.info(f"Fetching statistics for user {user_id} from {start_date} to {end_date}")
    
    return {
        "user_id": user_id,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "total_transactions": 0,
        "total_amount": 0.0,
        "average_transaction": 0.0
    }


def send_notification(user: User, message: str, notification_type: str = "info") -> bool:
    """
    Отправляет уведомление пользователю.
    
    Args:
        user: Объект пользователя
        message: Текст уведомления
        notification_type: Тип уведомления (info, warning, error)
        
    Returns:
        True если уведомление отправлено успешно
        
    Raises:
        ValueError: Если message пустой или notification_type невалиден
    """
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    valid_types = {"info", "warning", "error"}
    if notification_type not in valid_types:
        raise ValueError(f"Invalid notification type. Must be one of: {valid_types}")
    
    logger.info(f"Sending {notification_type} notification to user {user.user_id}: {message[:50]}...")
    
    return True


def create_user_account(username: str, email: str, role: UserRole) -> User:
    """
    Создает новый аккаунт пользователя.
    
    Args:
        username: Имя пользователя
        email: Email адрес
        role: Роль пользователя
        
    Returns:
        Объект пользователя
        
    Raises:
        ValueError: Если email невалиден или username пустой
    """
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")
    
    if not validate_email(email):
        raise ValueError("Invalid email address")
    
    user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return User(
        user_id=user_id,
        username=username.strip(),
        email=email.lower().strip(),
        role=role,
        created_at=datetime.now()
    )
