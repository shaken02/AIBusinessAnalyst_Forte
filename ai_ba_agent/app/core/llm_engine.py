"""LLM abstraction layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from app.config import settings
from app.core import prompt_templates
from app.utils.logger import logger


class LLMEngine:
    """Interface for all LLM providers."""

    def ask(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def generate_brd(self, context: str) -> str:
        prompt = prompt_templates.BRD_TEMPLATE.format(context=context)
        return self.ask(prompt)

    def generate_usecase(self, context: str) -> str:
        prompt = prompt_templates.USE_CASE_TEMPLATE.format(context=context)
        return self.ask(prompt)

    def generate_userstories(self, context: str) -> str:
        prompt = prompt_templates.USER_STORIES_TEMPLATE.format(context=context)
        return self.ask(prompt)

    def generate_plantuml(self, context: str) -> str:
        prompt = prompt_templates.PLANTUML_TEMPLATE.format(context=context)
        return self.ask(prompt)


@dataclass
class MockLLMEngine(LLMEngine):
    """Placeholder engine used until real integration is plugged in."""

    model_name: Optional[str] = settings.model.model_name

    def ask(self, prompt: str) -> str:
        lines = prompt.strip().splitlines()
        header = lines[0] if lines else "Ответ"
        return f"{header}\n\n{prompt_templates.MOCK_COMPLETION_SUFFIX}"


class TransformersEngine(LLMEngine):
    """Runs inference via HuggingFace transformers."""

    def __init__(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_cfg = settings.model
        logger.info("Loading transformers model %s", model_cfg.model_name)

        torch_dtype = None
        if model_cfg.dtype != "auto":
            torch_dtype = getattr(torch, model_cfg.dtype)

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_cfg.model_name,
            revision=model_cfg.revision,
            cache_dir=model_cfg.cache_dir,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_cfg.model_name,
            revision=model_cfg.revision,
            cache_dir=model_cfg.cache_dir,
            torch_dtype=torch_dtype,
            device_map=model_cfg.device,
        )
        self.generation_kwargs = {
            "temperature": model_cfg.temperature,
            "top_p": model_cfg.top_p,
            "max_new_tokens": model_cfg.max_new_tokens,
            "do_sample": True,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }

    def ask(self, prompt: str) -> str:
        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output_ids = self.model.generate(**inputs, **self.generation_kwargs)
        generated = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        completion = generated[len(prompt) :].strip()
        return completion or generated.strip()


class OllamaEngine(LLMEngine):
    """Runs inference via Ollama REST API."""

    def __init__(self) -> None:
        model_cfg = settings.model
        self.model_name = model_cfg.model_name
        self.api_url = model_cfg.ollama_api_url
        self.generation_kwargs = {
            "temperature": model_cfg.temperature,
            "top_p": model_cfg.top_p,
            "num_predict": model_cfg.max_new_tokens,
        }
        logger.info("Initialized Ollama engine for model %s at %s", self.model_name, self.api_url)

    def ask(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": self.generation_kwargs,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.RequestException as exc:
            logger.error("Ollama API request failed: %s", exc)
            raise RuntimeError(f"Ollama API error: {exc}") from exc


def create_engine() -> LLMEngine:
    provider = settings.model.provider
    if provider == "ollama":
        try:
            return OllamaEngine()
        except Exception as exc:  # pragma: no cover - fallback
            logger.error("Failed to init Ollama engine: %s", exc)
            return MockLLMEngine()
    if provider == "transformers":
        try:
            return TransformersEngine()
        except Exception as exc:  # pragma: no cover - fallback
            logger.error("Failed to init transformers engine: %s", exc)
            return MockLLMEngine()
    return MockLLMEngine()


__all__ = ["LLMEngine", "MockLLMEngine", "TransformersEngine", "OllamaEngine", "create_engine"]
