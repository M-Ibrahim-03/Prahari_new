"""Verbalize engine facts into warm spoken guidance (PRD §27).

🔴 The LLM is a TRANSLATOR, NEVER AN ORACLE.
It sees ONLY the immutable Facts dataclass and is strictly gated by pipeline/validate.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from adapters.llm.base import LLMProvider
from adapters.llm.template import TemplateLLMProvider
from pipeline.validate import validate_verbalized_text

SYSTEM_PROMPT_HI = """आप प्रहरी (PRAHARI) कृषि मौसम सहायक हैं।
आपका काम दिए गए मौसम और रोग के तथ्यों को किसान भाई-बहनों के लिए सरल, आदरणीय और स्पष्ट हिंदी में बताना है।
नियम:
1. केवल दिए गए तथ्यों पर आधारित रहें। अपने मन से कोई संख्या या समय न जोड़ें।
2. किसी भी दवा, कीटनाशक, फफूंदनाशक का नाम या खुराक (Dose) न बताएं।
3. उत्तर अधिकतम 40-50 शब्दों में रखें।
"""

SYSTEM_PROMPT_EN = """You are PRAHARI agriculture weather assistant.
Your task is to explain the provided physical disease facts in simple, respectful words.
Rules:
1. State ONLY facts provided. Never invent numbers or timing.
2. NEVER mention any chemical brand, fungicide, dose, or spray volume.
3. Keep response strictly under 50 words.
"""


@dataclass(frozen=True)
class Facts:
    field_name: str
    crop: str
    band: str
    dsv_today: int
    dsv_accum: int
    wet_hours: int
    min_temp_c: float
    mean_wet_temp_c: float
    spray_window: Optional[str] = None
    firing_model: str = ""
    firing_pathogen: str = ""


def build_fact_prompt(facts: Facts, lang: str = "hi") -> str:
    if lang == "hi":
        return f"""खेत: {facts.field_name}
फसल: {facts.crop}
स्थिति: {facts.band}
नमी अवधि: {facts.wet_hours} घंटे
गीले समय का तापमान: {facts.mean_wet_temp_c} °C
संचित रोग दबाव (DSV): {facts.dsv_accum}
छिड़काव समय: {facts.spray_window or 'लागू नहीं'}
"""
    return f"""Field: {facts.field_name}
Crop: {facts.crop}
Risk Band: {facts.band}
Wet Hours: {facts.wet_hours} h
Mean Wet Temp: {facts.mean_wet_temp_c} C
Accumulated DSV: {facts.dsv_accum}
Spray Timing: {facts.spray_window or 'N/A'}
"""


def render_fallback_template(facts: Facts, lang: str = "hi") -> str:
    """Deterministic fallback text if LLM is unavailable or gate rejects."""
    if lang == "hi":
        if facts.band == "act":
            win = f" उत्तम समय {facts.spray_window} है।" if facts.spray_window else ""
            return f"{facts.field_name} में {facts.crop} पर रोग का जोखिम है।{win} मौसम अनुकूल रहने पर तुरंत छिड़काव करें।"
        elif facts.band == "watch":
            return f"{facts.field_name} में रोग के अनुकूल मौसम बन रहा है। खेत की निगरानी रखें और दवा तैयार रखें।"
        return f"{facts.field_name} में आज मौसम सामान्य है। किसी छिड़काव की आवश्यकता नहीं है।"
    else:
        if facts.band == "act":
            win = f" Best window: {facts.spray_window}." if facts.spray_window else ""
            return f"High risk on {facts.field_name}.{win} Spray during favorable weather."
        elif facts.band == "watch":
            return f"Weather is turning favorable for disease on {facts.field_name}. Keep watch."
        return f"All clear on {facts.field_name}. No spraying needed today."


def verbalise(
    facts: Facts,
    lang: str = "hi",
    provider: Optional[LLMProvider] = None,
) -> tuple[str, bool]:
    """Verbalise facts. Returns (text, is_llm_generated).

    If provider fails or gate rejects, returns (fallback_template, False).
    """
    if provider is None:
        provider = TemplateLLMProvider()

    prompt = build_fact_prompt(facts, lang)
    system_instruction = SYSTEM_PROMPT_HI if lang == "hi" else SYSTEM_PROMPT_EN

    try:
        raw_output = provider.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.3,
            max_tokens=150,
        )
    except Exception:
        return render_fallback_template(facts, lang), False

    allowed_nums = {
        float(facts.dsv_today),
        float(facts.dsv_accum),
        float(facts.wet_hours),
        round(facts.min_temp_c, 1),
        round(facts.mean_wet_temp_c, 1),
    }

    # Pass through §27.5 gate
    gate = validate_verbalized_text(
        raw_output,
        expected_band=facts.band,
        allowed_numbers=allowed_nums,
        lang=lang,
    )

    if not gate.passed:
        # Rejection logged, clean template rendered (L4 degradation)
        return render_fallback_template(facts, lang), False

    return raw_output, True
