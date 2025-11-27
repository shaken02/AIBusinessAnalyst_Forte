"""Конфигурация для Code Review Backend."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Загружаем .env файл из корня проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class GitLabConfig(BaseModel):
    """Конфигурация GitLab API."""
    
    api_url: str = Field(
        default="https://gitlab.com/api/v4",
        description="GitLab API URL"
    )
    access_token: str = Field(
        ...,
        description="GitLab Personal Access Token с правами api, write_repository"
    )
    webhook_secret_token: Optional[str] = Field(
        default=None,
        description="Secret token для проверки webhook запросов"
    )


class GeminiConfig(BaseModel):
    """Конфигурация Gemini API."""
    
    api_key: str = Field(..., description="Google Gemini API key")
    model_name: str = Field(
        default="gemini-2.5-flash",
        description="Название модели Gemini"
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Temperature для генерации"
    )
    max_output_tokens: int = Field(
        default=8192,
        ge=256,
        le=32768,
        description="Максимальное количество токенов в ответе"
    )


class AppConfig(BaseModel):
    """Основная конфигурация приложения."""
    
    gitlab: GitLabConfig
    gemini: GeminiConfig
    debug: bool = Field(
        default=False,
        description="Режим отладки"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Host для FastAPI сервера"
    )
    port: int = Field(
        default=8001,
        ge=1,
        le=65535,
        description="Port для FastAPI сервера"
    )


def load_config() -> AppConfig:
    """Загружает конфигурацию из переменных окружения."""
    
    # GitLab конфигурация
    gitlab_token = os.getenv("GITLAB_ACCESS_TOKEN")
    if not gitlab_token:
        raise ValueError(
            "GITLAB_ACCESS_TOKEN не установлен. "
            "Создайте Personal Access Token в GitLab с правами api, write_repository"
        )
    
    gitlab_config = GitLabConfig(
        api_url=os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4"),
        access_token=gitlab_token,
        webhook_secret_token=os.getenv("GITLAB_WEBHOOK_SECRET_TOKEN")
    )
    
    # Gemini конфигурация
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_BA_GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError(
            "GEMINI_API_KEY не установлен. "
            "Установите переменную окружения GEMINI_API_KEY или AI_BA_GEMINI_API_KEY"
        )
    
    gemini_config = GeminiConfig(
        api_key=gemini_key,
        model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
        temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
        max_output_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "8192"))
    )
    
    return AppConfig(
        gitlab=gitlab_config,
        gemini=gemini_config,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001"))
    )


# Глобальный экземпляр конфигурации
config = load_config()
