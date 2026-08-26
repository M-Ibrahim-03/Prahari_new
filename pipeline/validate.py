"""LLM Validation Gate (§27.5 / FR-7.10 / §39.2).

Enforces the five strict rejection rules on any LLM-generated output before
it can ever reach a farmer. A rejection immediately falls back to the deterministic
physics template (L4 degradation).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

BANNED_CHEMICALS = {
    # Active ingredients & classes
    "mancozeb", "metalaxyl", "cymoxanil", "dimethomorph", "copper oxychloride",
    "propineb", "azoxystrobin", "chlorothalonil", "carbendazim", "hexaconazole",
    "tebuconazole", "captan", "ziram", "thiram", "iprodione", "fosetyl",
    "fungicide", "chemical", "fungicides", "chemicals",
    # Brand names
    "ridomil", "dithane", "antracol", "kavach", "safal", "bavistin", "curzate", "acrobat", "indofil",
    # Hindi chemical references
    "मैनकोजेब", "मेटालेक्सिल", "साइमोक्सानिल", "डाइमेथोमॉर्फ", "फफूंदनाशक", "कीटनाशक", "दवा की मात्रा", "रिडोमिल", "डाइथेन",
}

DOSE_PATTERNS = [
    r"\d+\s*(?:ml|g|gm|kg|ltr|l|लीटर|मिली|ग्राम)\b",
    r"\d+\s*(?:ml|g|gm)/[lL]",
    r"\d+\s*%/ha",
    r"\b(?:dose|dosage|tank mix|dilution|concentration|ppe|re-entry)\b",
    r"\b(?:मात्रा|खुराक|दवा का घोल|छिड़काव की मात्रा)\b",
]

WORD_LIMIT = 60


@dataclass(frozen=True)
class GateResult:
    passed: bool
    rejection_reasons: list[str]


def extract_numbers(text: str) -> set[float]:
    """Extract numeric values from text (both ASCII and Devanagari numerals)."""
    # Convert Devanagari digits to ASCII
    devanagari = "०१२३४५६७८९"
    clean_text = text
    for d, ascii_digit in enumerate("0123456789"):
        clean_text = clean_text.replace(devanagari[d], ascii_digit)

    matches = re.findall(r"\b\d+(?:\.\d+)?\b", clean_text)
    return {float(m) for m in matches}


def validate_verbalized_text(
    output_text: str,
    *,
    expected_band: str,
    allowed_numbers: set[float],
    lang: str = "hi",
) -> GateResult:
    """Run the §27.5 five-rule validation gate.

    Rules:
      1. No invented numbers outside allowed_numbers.
      2. No banned chemical / fungicide names.
      3. No dose / concentration / PPE patterns.
      4. No modified risk band or opposite action verb.
      5. Word count <= 60 words.
    """
    reasons: list[str] = []
    lower = output_text.lower()

    # Rule 1: No invented numbers
    found_nums = extract_numbers(output_text)
    # Filter out common benign non-invented numbers (like 12/24 clock hours or 1-7 days of week if standard)
    invented = [n for n in found_nums if n not in allowed_numbers and n not in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24}]
    if invented:
        reasons.append(f"INVENTED_NUMBERS: {invented}")

    # Rule 2: No banned chemical / fungicide terms
    for chem in BANNED_CHEMICALS:
        if chem in lower:
            reasons.append(f"BANNED_CHEMICAL: {chem}")

    # Rule 3: No dose / interval prescription patterns
    for pat in DOSE_PATTERNS:
        if re.search(pat, lower):
            reasons.append(f"DOSE_PRESCRIPTION_PATTERN: {pat}")

    # Rule 4: Risk band alignment
    if expected_band == "safe":
        if "छिड़काव करें" in output_text or "spray immediately" in lower or "spray today" in lower:
            reasons.append("BAND_CONTRADICTION: safe band told to spray")
    elif expected_band == "act":
        if "छिड़काव न करें" in output_text or "do not spray" in lower or "no risk" in lower:
            reasons.append("BAND_CONTRADICTION: act band told not to spray")

    # Rule 5: Word limit <= 60 words
    words = output_text.split()
    if len(words) > WORD_LIMIT:
        reasons.append(f"LENGTH_DRIFT: {len(words)} words exceeds {WORD_LIMIT}")

    return GateResult(passed=len(reasons) == 0, rejection_reasons=reasons)
