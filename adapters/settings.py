"""Secret loading — the single place keys enter the process. Adapters only; never engine.

Reads from the environment (a gitignored .env in dev, GitHub Secrets / Vercel env in
prod). 🔴 Nothing here is ever hard-coded, and 🔴 only ``maptiler_key`` is safe to send
to the browser, and only when domain-restricted (PRD §33.2).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:  # dev convenience; in CI the env is already populated from GitHub Secrets
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name!r}. "
            f"Copy .env.example to .env and fill it in (or set it in GitHub Secrets)."
        )
    return value


@dataclass(frozen=True)
class Settings:
    """Resolved secrets. Server-side only, except ``maptiler_key``."""

    gemini_api_key: str
    supabase_url: str
    supabase_service_key: str  # 🔴 bypasses RLS — never expose to the browser
    maptiler_key: str          # browser-safe only when domain-restricted
    opentopo_key: str


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=_require("GEMINI_API_KEY"),
        supabase_url=_require("SUPABASE_URL"),
        supabase_service_key=_require("SUPABASE_SERVICE_KEY"),
        maptiler_key=os.environ.get("MAPTILER_KEY", "").strip(),
        opentopo_key=os.environ.get("OPENTOPO_KEY", "").strip(),
    )
