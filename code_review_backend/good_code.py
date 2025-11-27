"""Модуль с хорошими практиками программирования."""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def calculate_total_price(items: list[Dict[str, Any]], discount: Optional[float] = None) -> float:
    """
    Рассчитывает общую стоимость товаров с учетом скидки.
    
    Args:
        items: Список товаров с полями 'price' и 'quantity'
        discount: Процент скидки (от 0 до 100), опционально
        
    Returns:
        Общая стоимость после применения скидки
        
    Raises:
        ValueError: Если цена или количество отрицательные, или скидка вне диапазона
    """
    if not items:
        return 0.0
    
    total = 0.0
    for item in items:
        price = item.get('price', 0)
        quantity = item.get('quantity', 0)
        
        if price < 0 or quantity < 0:
            raise ValueError("Цена и количество должны быть неотрицательными")
        
        total += price * quantity
    
    if discount is not None:
        if not 0 <= discount <= 100:
            raise ValueError("Скидка должна быть от 0 до 100 процентов")
        total = total * (1 - discount / 100)
    
    return round(total, 2)


def format_user_data(user_id: str, username: str, email: str) -> Dict[str, Any]:
    """
    Форматирует данные пользователя для безопасного логирования.
    
    Args:
        user_id: Уникальный идентификатор пользователя
        username: Имя пользователя
        email: Электронная почта
        
    Returns:
        Словарь с отформатированными данными
    """
    logger.info(f"Formatting user data for user_id: {user_id}")
    
    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "formatted_at": datetime.now().isoformat(),
        "status": "active"
    }

