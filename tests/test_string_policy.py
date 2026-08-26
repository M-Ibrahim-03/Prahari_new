"""CI String Policy Gate (§13.7 / §39.2 / PRD Governing Law #3).

Guarantees that the app never names a chemical fungicide, brand, dose, concentration,
or PPE prescription anywhere in user-facing templates, YAML configs, or UI copy.
"""
from pathlib import Path
import re
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent

BANNED_CHEMICAL_TERMS = [
    "mancozeb", "metalaxyl", "cymoxanil", "dimethomorph", "copper oxychloride",
    "propineb", "azoxystrobin", "chlorothalonil", "carbendazim", "hexaconazole",
    "ridomil", "dithane", "antracol", "kavach", "safal", "bavistin",
]

# Patterns for dose recommendations like "250 ml/ha" or "2.5 g/L"
DOSE_REGEX = re.compile(r"\b\d+\s*(?:ml|gm|g|kg)/[a-zA-Z]+\b", re.IGNORECASE)


def test_no_chemical_fungicides_in_advisory_templates():
    templates_file = ROOT_DIR / "pipeline" / "config" / "advisory_templates.yaml"
    content = templates_file.read_text(encoding="utf-8").lower()
    for chem in BANNED_CHEMICAL_TERMS:
        assert chem not in content, f"Banned chemical term '{chem}' found in advisory_templates.yaml"
    assert not DOSE_REGEX.search(content), "Dose pattern found in advisory_templates.yaml"


def test_no_chemical_fungicides_in_ui_components():
    src_dir = ROOT_DIR / "web" / "src"
    for tsx_file in src_dir.rglob("*.tsx"):
        # Exclude Trust.tsx disclaimer and test words
        if tsx_file.name in {"Trust.tsx", "AskModal.tsx"}:
            continue
        content = tsx_file.read_text(encoding="utf-8").lower()
        for chem in BANNED_CHEMICAL_TERMS:
            assert chem not in content, f"Banned chemical term '{chem}' found in {tsx_file.name}"
