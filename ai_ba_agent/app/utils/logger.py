"""Centralized logger configuration."""

from __future__ import annotations

import os
import sys
from typing import Optional

from loguru import logger

_LOG_LEVEL = os.getenv("AI_BA_LOG_LEVEL", "INFO").upper()


def configure_logger(extra_sink: Optional[str] = None) -> None:
    """Configure loguru logger once per process."""

    logger.remove()
    logger.add(sys.stderr, level=_LOG_LEVEL, colorize=True, enqueue=True)

    if extra_sink:
        logger.add(extra_sink, level=_LOG_LEVEL, rotation="1 week", enqueue=True)


# Configure immediately on import for convenience.
configure_logger()

__all__ = ["logger", "configure_logger"]
