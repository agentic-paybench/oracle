"""Static site manifest + published posture (M7)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "docs" / "site"
INDEX = SITE / "index.json"
POSTURE = SITE / "posture.json"
LIVE_CONFIG = REPO / "config" / "regulatory_posture.live.json"


def test_index_lists_expected_live_surfaces():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    surfaces = index["surfaces"]
    for key in ("tier2_capabilities", "tier1_methodology", "schema", "adr", "roadmap", "did"):
        assert key in surfaces, f"index missing surface {key}"


def test_index_omits_named_rail_table_while_s21_closed():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    surfaces_blob = json.dumps(index["surfaces"]).lower()
    # No live surface points at the ranking / named-rail table.
    assert "finality-run" not in surfaces_blob
    assert "ranking" not in surfaces_blob
    assert "named_rail_results_table" not in surfaces_blob
    # It is documented as gated off instead.
    assert "G_S21" in index["gated_off"]["named_rail_results_table"]


def test_404_page_present():
    assert (SITE / "404.html").is_file(), "docs/site/404.html missing (Pages soft-404 fallback)"


def test_posture_json_matches_live_config():
    posture = json.loads(POSTURE.read_text(encoding="utf-8"))
    live = json.loads(LIVE_CONFIG.read_text(encoding="utf-8"))
    assert posture["gates"] == live["gates"]
    assert posture["regulatory_posture"] == live["regulatory_posture"]
    assert posture["gates"]["G_S21"] == "closed"
    assert "scored_query" in posture["surfaces_inert"]
