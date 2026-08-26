"""LLM Provider Interface Protocol (PRD §27). Pure typing interface."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, prompt: str, *, system_instruction: str = "", temperature: float = 0.3, max_tokens: int = 200) -> str:
        """Generate text from prompt. Must be deterministic with low temperature."""
        ...
