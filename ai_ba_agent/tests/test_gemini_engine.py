"""Integration smoke test for Gemini LLM engine."""

from __future__ import annotations

import os
import unittest

from app.core.llm_engine import GeminiEngine


@unittest.skipUnless(
    os.getenv("AI_BA_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
    "Gemini API key is not set; skipping live connectivity test.",
)
class TestGeminiEngineConnectivity(unittest.TestCase):
    """Validate that Gemini API responds with text."""

    def test_generate_content_returns_text(self) -> None:
        engine = GeminiEngine()
        reply = engine.ask("Проверка подключения. Ответь одним словом: OK.")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
