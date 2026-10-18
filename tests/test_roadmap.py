"""Tier-3 roadmap: labelled, carries no measurements."""

import re
from pathlib import Path

ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "site" / "roadmap.md"

# Measurement / ranking vocabulary that must never appear on a Tier-3 page.
_FORBIDDEN = ["median", "sigma", "σ", "μ", "bradley", "rank", "pass@k", "wilson"]


def test_roadmap_is_labelled():
    """The '(no measurement)' labels were removed on 2026-10-18; the page
    still says, in its own
    words, that nothing on it is measured."""
    text = " ".join(ROADMAP.read_text(encoding="utf-8").lower().split())
    assert "declared direction, not a benchmarked result" in text


def test_roadmap_has_no_measurements():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    for term in _FORBIDDEN:
        assert term not in text, f"roadmap contains measurement term: {term!r}"
    # No calibrated (decimal) numbers. Resolvable identifiers (DOIs inside
    # URLs) are provenance pointers, not measurements; strip them first.
    scrubbed = re.sub(r"<?https?://\S+>?", "", text)
    assert not re.search(r"\d+\.\d+", scrubbed), "roadmap contains a decimal measurement"
