"""Tier-2 widening: structural cells are documented facts with provenance.

Builds every subject in memory from ingest/data/ (no signing, no network) and
checks: schema validity; no 'measured' label while the DIM-04 measured annexes
are held; the notice travels with every widened subject; no ranking key at any
depth; our own statements carry no merit, recommendation or commercial term the
release gate blocks; the Machine Payments Protocol is never written bare.
"""

import json
import re
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from ingest import build_capabilities as bc  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO / "schema" / "capability.schema.json").read_text(encoding="utf-8"))

_FORBIDDEN_KEYS = {"score", "rank", "recommendation"}
# Our own words only (statements and values). Quoted source text lives in the
# sourcing sheet, never in a served cell.
_BLOCKED = re.compile(
    r"\b(?:best|worst|fastest|slowest|cheapest|winner|rank(?:s|ed|ing)?|"
    r"recommend(?:s|ed|ation)?|sponsor(?:s|ed|ship)?|affiliate|superior|inferior|"
    r"outperform(?:s|ed)?|choose|pick)\b",
    re.I,
)
_BARE_MPP = re.compile(r"\bMPP\b")
_DASHES = re.compile("[\u2013\u2014]")


def _subjects():
    rails = json.loads(bc.FACTS.read_text(encoding="utf-8"))["rails"]
    st = bc._load_structural()
    return [bc.capability_subject(r, st["rails"].get(r["railId"]), st["meta"]) for r in rails], st


def _deep_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _deep_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _deep_keys(v)


def _own_text(subject):
    """Statements and string values of structural cells (not URLs, not the notice)."""
    for name in bc.STRUCTURAL_FIELDS:
        cell = subject.get(name)
        if not cell:
            continue
        yield name, cell.get("statement", "")
        if isinstance(cell.get("value"), str):
            yield name, cell["value"]
    rs = subject["bundle"]["refundSupport"]
    if isinstance(rs, dict):
        yield "refundSupport", rs.get("statement", "")
        for k in rs.get("value", []):
            for v in k.values():
                yield "refundSupport", v


def test_every_built_subject_validates():
    subjects, _ = _subjects()
    for s in subjects:
        vc = bc.unsigned_vc({"railId": s["railId"], "railName": s["railName"],
                             "settlesIndependently": s["settlesIndependently"]},
                            "did:example:test")
        vc["credentialSubject"] = s
        jsonschema.validate(instance=vc, schema=SCHEMA)


def test_no_cell_is_labelled_measured():
    subjects, _ = _subjects()
    for s in subjects:
        for name in bc.STRUCTURAL_FIELDS:
            if name in s:
                assert s[name]["provenance"]["label"] != "measured", f"{s['railId']}.{name}"


def test_builder_refuses_a_measured_label():
    cell = {"value": "x", "disposition": "positive", "statement": "x",
            "provenance": {"label": "measured", "sources": [], "retrievedAt": "2026-10-09",
                           "layer": "protocol"}}
    with pytest.raises(bc.MeasuredLabelRefused):
        bc.capability_subject({"railId": "RX", "railName": "RX", "settlesIndependently": True},
                              {"displayName": "RX", "cells": {"feeBearer": cell}},
                              {"evenHandedStatement": "x", "feeSourceStatement": "x",
                               "statementsUrl": "https://oracle.agentic-paybench.dev/"})


def test_widened_subjects_carry_the_notice():
    subjects, _ = _subjects()
    for s in subjects:
        widened = any(n in s for n in bc.STRUCTURAL_FIELDS) or isinstance(s["bundle"]["refundSupport"], dict)
        if widened:
            assert s["notice"]["documentationStatement"] == bc.DOCUMENTATION_STATEMENT
            assert s["notice"]["fixedOrderingStatement"] == bc.FIXED_ORDERING_STATEMENT
            assert "feeBearer" in s["notice"]["feeQuotation"]["appliesTo"]


def test_no_ranking_key_at_any_depth():
    subjects, _ = _subjects()
    for s in subjects:
        assert not ({k.lower() for k in _deep_keys(s)} & _FORBIDDEN_KEYS), s["railId"]


def test_own_text_is_free_of_gate_blocked_terms_dashes_and_bare_mpp():
    subjects, _ = _subjects()
    for s in subjects:
        for name, text in _own_text(s):
            assert not _BLOCKED.search(text), f"{s['railId']}.{name}: {text!r}"
            assert not _DASHES.search(text), f"{s['railId']}.{name} carries a dash"
            assert not _BARE_MPP.search(text), f"{s['railId']}.{name} writes bare MPP"


def test_display_names_are_unique():
    _, st = _subjects()
    names = [r["displayName"] for r in st["rails"].values()]
    assert len(names) == len(set(names))


FEE_BEARER_VARIANT = (
    "These fee facts are a quotation of published fee documentation, not a "
    "recommendation: no rail is endorsed, no ordering implies a best buy, and no "
    "rail is being suggested for use."
)


def test_fee_bearer_variant_is_pinned():
    """The builder constant and the schema const carry the ruled variant byte for byte."""
    assert bc.FEE_QUOTATION_STATEMENT == FEE_BEARER_VARIANT
    schema = json.loads((REPO / "schema" / "capability.schema.json").read_text(encoding="utf-8"))
    assert FEE_BEARER_VARIANT in json.dumps(schema)
    assert "These figures are a quotation of a published fee schedule" not in json.dumps(schema)


FEE_EVEN_HANDED_COMPANION = (
    "Every rail's fee facts are quoted from that rail's own published fee "
    "documentation, retrieved on the same date by the same procedure."
)
FEE_SOURCE_COMPANION = (
    "Each fee fact is quoted from the rail's own published fee documentation at the "
    "source URL given beside it, retrieved on 2026-10-09."
)


def test_fee_companion_statements_describe_facts_not_figures():
    """The two companion statements describe fee facts and fee documentation, not figures and a schedule,
    because the fee-adjacent cells carry neither; the retrieval-date and same-procedure phrases are kept."""
    assert bc.FEE_EVEN_HANDED_STATEMENT == FEE_EVEN_HANDED_COMPANION
    schema = json.dumps(json.loads((REPO / "schema" / "capability.schema.json").read_text(encoding="utf-8")))
    assert FEE_EVEN_HANDED_COMPANION in schema
    data = json.loads((REPO / "ingest" / "data" / "rail-tier2-structural.json").read_text(encoding="utf-8"))
    assert data["meta"]["feeSourceStatement"] == FEE_SOURCE_COMPANION
    page = (REPO / "docs" / "site" / "tier2" / "statements.md").read_text(encoding="utf-8")
    assert FEE_EVEN_HANDED_COMPANION in page and FEE_SOURCE_COMPANION in page
    for text in (schema, json.dumps(data["meta"]), page):
        assert "published fee schedule" not in text and "published schedule" not in text
        assert "Each figure" not in text


def test_offline_verifiability_cell_on_every_rail():
    """The thirteenth field, offline verifiability: one documentation-profile cell per rail, each with
    its sources dated, the even-handed statement naming thirteen questions on the data, the page and the
    notice alike."""
    subjects, st = _subjects()
    assert "offlineVerifiability" in bc.STRUCTURAL_FIELDS
    assert "offlineVerifiability" in SCHEMA["properties"]["credentialSubject"]["dependentRequired"]
    for s in subjects:
        cell = s["offlineVerifiability"]
        assert cell["provenance"]["profile"] == "documentation_profile", s["railId"]
        assert cell["provenance"]["label"] == "documentation-derived", s["railId"]
        assert cell["provenance"]["sources"] and all(src["retrievedAt"] == "2026-10-10"
                                                      for src in cell["provenance"]["sources"]), s["railId"]
        assert s["notice"]["evenHandedStatement"] == st["meta"]["evenHandedStatement"]
    page = (REPO / "docs" / "site" / "tier2" / "statements.md").read_text(encoding="utf-8")
    assert st["meta"]["evenHandedStatement"] in page
    assert "thirteen questions" in st["meta"]["evenHandedStatement"]
    assert "twelve questions" not in page


def test_option_c_envelope():
    """The notice envelope: typed flags, a pointer to a served page, a per-cell profile."""
    subjects, _ = _subjects()
    page = REPO / "docs" / "site" / "tier2" / "statements.md"
    assert page.is_file(), "statement page missing"
    for s in subjects:
        if "notice" not in s:
            continue
        n = s["notice"]
        assert n["kind"] == "documentation_profile" and n["feeQuotation"]["kind"] == "fee_quotation"
        assert n["statementsUrl"].endswith("/tier2/statements.md")
        assert bc.DOCUMENTATION_STATEMENT in page.read_text(encoding="utf-8")
        # Fee-bearer variant of the fee-quotation sentence.
        assert n["feeQuotation"]["quotationStatement"] == FEE_BEARER_VARIANT
        assert FEE_BEARER_VARIANT in page.read_text(encoding="utf-8")
        assert "These figures are a quotation" not in json.dumps(n)
        for name in bc.STRUCTURAL_FIELDS:
            if name in s:
                want = "fee_quotation" if name in bc.FEE_ADJACENT else "documentation_profile"
                assert s[name]["provenance"]["profile"] == want, (s["railId"], name)
                assert all(src["retrievedAt"] for src in s[name]["provenance"]["sources"])
