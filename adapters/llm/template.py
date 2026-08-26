"""Deterministic Template LLM Provider (PRD §27.4 Fallback). Pure / Zero-Network."""
from __future__ import annotations


class TemplateLLMProvider:
    """Always-available deterministic fallback provider (L4 degradation)."""

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str = "",
        temperature: float = 0.3,
        max_tokens: int = 200,
    ) -> str:
        # Prompt contains the structured facts
        return prompt.strip()
