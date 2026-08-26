"""Gemini LLM Provider (PRD §27.2 / Free-tier AI Studio). Server-side only."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
import os


class GeminiLLMProvider:
    """Invokes Google Gemini 1.5/2.0 API with strict low temperature."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str = "",
        temperature: float = 0.3,
        max_tokens: int = 200,
    ) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return ""
        except Exception as e:
            raise RuntimeError(f"Gemini API invocation failed: {e}") from e
