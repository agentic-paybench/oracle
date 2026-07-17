"""ADR register presence + invariant declarations for the public ADR set.

The public oracle repo carries only the ADRs written for an external reader:
ADR-007 (Intent-Free Oracle) and ADR-009 (canEmit PDP). The ADRs live at
repo-root ``docs/adr/`` (one level above the ``tests/`` dir).
"""

from pathlib import Path

ADR_DIR = Path(__file__).resolve().parents[1] / "docs" / "adr"

REQUIRED = {
    "ADR-007": "ADR-007-intent-free-oracle.md",
    "ADR-009": "ADR-009-canemit-pdp.md",
}


def _read(key: str) -> str:
    return (ADR_DIR / REQUIRED[key]).read_text(encoding="utf-8")


def test_required_adrs_present():
    for key, fname in REQUIRED.items():
        assert (ADR_DIR / fname).is_file(), f"missing {fname}"


def test_only_public_adrs_present():
    # The public repo carries no other decision records; anything else in
    # docs/adr/ must be deliberately added here and to public-manifest.toml.
    actual = {p.name for p in ADR_DIR.glob("*.md")}
    assert actual == set(REQUIRED.values()), f"unexpected ADR files: {actual}"


def test_no_needs_writing_stub():
    for key in REQUIRED:
        assert "NEEDS-WRITING" not in _read(key), f"{key} still a stub"


def test_adr009_declares_four_gate_keys():
    body = _read("ADR-009")
    for gate in ("G_AUTH", "G_QF", "G_S21", "G_CUSTODY"):
        assert gate in body, f"ADR-009 missing gate {gate}"
    assert "canEmit(mechanic, context)" in body
    assert "default deny" in body.lower()


def test_adr007_declares_invariant():
    body = _read("ADR-007")
    for param in ("amount", "payee", "asset-to-pay"):
        assert param in body, f"ADR-007 missing forbidden param {param}"
    for key in ("score", "rank", "recommendation"):
        assert key in body, f"ADR-007 missing forbidden response key {key}"
