"""Coordinates dialog context with LLM generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.llm_engine import LLMEngine, create_engine
from app.generators import (
    brd_generator,
    pdf_generator,
    plantuml_generator,
    usecase_generator,
    userstories_generator,
)
from app.utils.logger import logger
from app.utils.state import ConversationState


@dataclass
class DocumentBundle:
    brd: str
    usecase: str
    userstories: str
    plantuml: str

    def as_dict(self) -> dict:
        return {
            "BRD": self.brd,
            "Use Case": self.usecase,
            "User Stories": self.userstories,
            "PlantUML": self.plantuml,
        }

    def to_pdf(self, project_name: str = "Business Requirements Document") -> bytes:
        return pdf_generator.markdown_to_pdf_bytes(self.as_dict(), project_name=project_name)


class Orchestrator:
    def __init__(self, engine: Optional[LLMEngine] = None, model_name: Optional[str] = None):
        self.engine = engine or create_engine(model_name=model_name)

    def is_ready(self, state: ConversationState) -> bool:
        return state.is_complete()

    def generate_documents(self, state: ConversationState) -> DocumentBundle:
        if not self.is_ready(state):
            raise ValueError("Не все поля заполнены")

        context = state.as_markdown_context()
        logger.info("Generating documents for %s fields", len(state.answers))

        return DocumentBundle(
            brd=brd_generator.generate_brd(context, self.engine),
            usecase=usecase_generator.generate_usecase(context, self.engine),
            userstories=userstories_generator.generate_userstories(context, self.engine),
            plantuml=plantuml_generator.generate_plantuml(context, self.engine),
        )


__all__ = ["Orchestrator", "DocumentBundle"]
