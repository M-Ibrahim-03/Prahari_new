"""Adversarial tests for §27.5 LLM validation gate.

Tests each of the five rejection rules with poisoned mock LLM outputs.
Asserts that poisoned outputs are rejected and cleanly fall back to templates.
"""
import pytest

from pipeline.validate import validate_verbalized_text
from pipeline.verbalise import Facts, verbalise


class PoisonedLLMProvider:
    def __init__(self, poisoned_text: str):
        self.poisoned_text = poisoned_text

    def generate(self, prompt: str, **kwargs) -> str:
        return self.poisoned_text


SAMPLE_FACTS = Facts(
    field_name="बड़ा खेत",
    crop="आलू",
    band="act",
    dsv_today=4,
    dsv_accum=22,
    wet_hours=8,
    min_temp_c=18.0,
    mean_wet_temp_c=22.0,
    spray_window="मंगलवार सुबह ६–९ बजे",
)


def test_gate_rejects_invented_numbers():
    # LLM invents 45.5% humidity or 500 liters
    poisoned = "बड़ा खेत में रोग का खतरा है। 500 लीटर पानी का उपयोग करें।"
    res = validate_verbalized_text(poisoned, expected_band="act", allowed_numbers={4.0, 22.0, 8.0, 18.0})
    assert not res.passed
    assert any("INVENTED_NUMBERS" in r for r in res.rejection_reasons)


def test_gate_rejects_banned_chemical_names():
    # Poisoned with mancozeb / ridomil
    poisoned = "बड़ा खेत में झुलसा है। Mancozeb या Ridomil का प्रयोग करें।"
    res = validate_verbalized_text(poisoned, expected_band="act", allowed_numbers={4.0, 22.0, 8.0, 18.0})
    assert not res.passed
    assert any("BANNED_CHEMICAL" in r for r in res.rejection_reasons)


def test_gate_rejects_dose_and_concentration_patterns():
    # Poisoned with dose pattern 2.5 g/L
    poisoned = "मौसम अनुकूल है, 2.5 g/L का घोल बनाकर छिड़कें।"
    res = validate_verbalized_text(poisoned, expected_band="act", allowed_numbers={4.0, 22.0, 8.0, 18.0, 2.5})
    assert not res.passed
    assert any("DOSE_PRESCRIPTION_PATTERN" in r for r in res.rejection_reasons)


def test_gate_rejects_band_contradiction():
    # Act band told not to spray
    poisoned = "बड़ा खेत में कोई समस्या नहीं है, आज छिड़काव न करें।"
    res = validate_verbalized_text(poisoned, expected_band="act", allowed_numbers={4.0, 22.0, 8.0, 18.0})
    assert not res.passed
    assert any("BAND_CONTRADICTION" in r for r in res.rejection_reasons)


def test_gate_rejects_length_drift():
    # Output with > 60 words
    poisoned = " ".join(["सावधानी"] * 70)
    res = validate_verbalized_text(poisoned, expected_band="act", allowed_numbers={4.0, 22.0, 8.0, 18.0})
    assert not res.passed
    assert any("LENGTH_DRIFT" in r for r in res.rejection_reasons)


def test_verbalise_falls_back_to_template_on_rejection():
    provider = PoisonedLLMProvider("Ridomil 250 ml छिड़कें")
    text, is_llm = verbalise(SAMPLE_FACTS, lang="hi", provider=provider)
    assert not is_llm
    assert "Ridomil" not in text
    assert "250 ml" not in text
    assert "बड़ा खेत" in text
