"""Centralized configuration objects for the AI Business Analyst MVP."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# Load .env file if it exists
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

MODEL_CONFIG_PATH = PROJECT_ROOT / "models" / "model_config.json"


class AppSettings(BaseModel):
    """Streamlit/UI level configuration."""

    name: str = "AI Business Analyst"
    debug: bool = False
    chat_history_limit: int = Field(20, ge=5, le=200)
    transcript_dir: Path = PROJECT_ROOT / "docs" / "examples"


class ModelSettings(BaseModel):
    """Runtime configuration for the selected LLM backend."""

    provider: Literal["transformers", "ollama", "mlx", "llama.cpp", "gemini"] = "ollama"
    model_name: str = "gemma:latest"
    ollama_api_url: str = "http://localhost:11434/api/generate"
    gemini_api_key: Optional[str] = None
    gemini_model_name: str = "gemini-2.5-flash"
    revision: Optional[str] = None
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    top_p: float = Field(0.9, gt=0.0, le=1.0)
    max_new_tokens: int = Field(512, ge=32, le=8192)
    device: str = "auto"
    dtype: Literal["auto", "float32", "bfloat16", "float16"] = "auto"
    cache_dir: Path = PROJECT_ROOT / "models" / "cache"

    @validator("cache_dir", pre=True)
    def _expand_cache_dir(cls, value: Any) -> Path:  # noqa: D401
        """Ensure cache_dir is always a Path."""
        if isinstance(value, Path):
            return value
        return Path(value).expanduser().resolve()


class OrchestratorSettings(BaseModel):
    """Parameters for orchestrating the generation pipeline."""

    default_language: str = "ru"
    allow_partial_generation: bool = True
    pdf_output_dir: Path = PROJECT_ROOT / "docs" / "examples"


class Settings(BaseModel):
    """Top-level settings container."""

    project_root: Path = PROJECT_ROOT
    app: AppSettings = AppSettings()
    model: ModelSettings = ModelSettings()
    orchestrator: OrchestratorSettings = OrchestratorSettings()


def _load_model_config_from_disk() -> Dict[str, Any]:
    if not MODEL_CONFIG_PATH.exists():
        return {}

    with MODEL_CONFIG_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _settings_from_env() -> Dict[str, Any]:
    """Allow lightweight overriding via environment variables."""

    overrides: Dict[str, Any] = {}
    model_overrides: Dict[str, Any] = {}

    env_map = {
        "AI_BA_MODEL_NAME": "model_name",
        "AI_BA_MODEL_PROVIDER": "provider",
        "AI_BA_MODEL_DEVICE": "device",
        "AI_BA_MODEL_TEMPERATURE": "temperature",
        "AI_BA_MODEL_MAX_NEW_TOKENS": "max_new_tokens",
        "AI_BA_OLLAMA_URL": "ollama_api_url",
        "AI_BA_GEMINI_API_KEY": "gemini_api_key",
    }

    for env_key, field_name in env_map.items():
        value = os.getenv(env_key)
        if value is None:
            continue
        if field_name in {"temperature"}:
            model_overrides[field_name] = float(value)
        elif field_name in {"max_new_tokens"}:
            model_overrides[field_name] = int(value)
        else:
            model_overrides[field_name] = value

    if model_overrides:
        overrides["model"] = model_overrides

    app_debug = os.getenv("AI_BA_DEBUG")
    if app_debug is not None:
        overrides.setdefault("app", {})["debug"] = app_debug.lower() in {"1", "true", "yes"}

    return overrides


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    file_overrides = {"model": _load_model_config_from_disk()} if MODEL_CONFIG_PATH.exists() else {}
    env_overrides = _settings_from_env()

    # Правильно объединяем вложенные словари
    merged: Dict[str, Any] = {}
    merged.update(file_overrides)
    
    # Объединяем env_overrides, но не перезаписываем полностью вложенные словари
    for key, value in env_overrides.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Объединяем вложенные словари
            merged[key] = {**merged[key], **value}
        else:
            # Обычное обновление для не-словарей
            merged[key] = value

    return Settings(**merged)


settings = get_settings()
