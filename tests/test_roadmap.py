"""Tier-3 roadmap: labelled, carries no measurements (M8)."""

import re
from pathlib import Path

ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "site" / "roadmap.md"

# Measurement / ranking vocabulary that must never appear on a Tier-3 page.
_FORBIDDEN = ["median", "sigma", "σ", "μ", "bradley", "rank", "pass@k", "wilson"]


def test_roadmap_is_labelled():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    assert "roadmap (no measurement)" in text


def test_roadmap_has_no_measurements():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    for term in _FORBIDDEN:
        assert term not in text, f"roadmap contains measurement term: {term!r}"
    # No calibrated (decimal) numbers.
    assert not re.search(r"\d+\.\d+", text), "roadmap contains a decimal measurement"
