"""Mutation drill: prove the gates are load-bearing, not decorative.

The standing CI invariants assert the shipped live config keeps the
named-rail table (published-rankings) and the scored query (scored-query)
inert. This drill flips each gate open in a MUTATED COPY of the live config
(never the shipped file) and asserts the PDP would then emit - proving that
(a) the gate causally controls emission, and (b) the standing invariant
tests would go red if the shipped config were ever mutated. A gate whose
mutation changed nothing would be an assertion in prose, not a control.
"""

import json
from dataclasses import replace
from pathlib import Path

from pdp import EmitContext, can_emit, load_config, load_named

_LIVE_JSON = Path(__file__).resolve().parents[1] / "config" / "regulatory_posture.live.json"


def test_drill_s21_open_would_emit_named_table():
    live = load_named("live")
    # Standing invariant (what CI asserts on the shipped config):
    assert not can_emit("published-rankings", EmitContext(), live).allowed
    # Drill: same config with G_S21 flipped open.
    mutated = replace(live, gates={**live.gates, "G_S21": "open"})
    assert can_emit("published-rankings", EmitContext(), mutated).allowed


def test_drill_auth_open_would_emit_scored(spine):
    live = load_named("live")
    rails = tuple(spine.rails.values())
    ctx = EmitContext(rails=rails)
    # Standing invariant:
    assert not can_emit("scored-query", ctx, live).allowed
    # Drill: G_AUTH flipped open.
    mutated = replace(live, gates={**live.gates, "G_AUTH": "open"})
    assert can_emit("scored-query", ctx, mutated).allowed


def test_drill_file_level_tamper_is_detectable(tmp_path):
    # File-layer variant: a tampered copy of the shipped live config is
    # loadable and distinguishable - the exact predicate the CI invariant
    # checks (gate_open is False) flips, so CI would go red.
    data = json.loads(_LIVE_JSON.read_text(encoding="utf-8"))
    data["gates"]["G_S21"] = "open"
    tampered = tmp_path / "regulatory_posture.live.json"
    tampered.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(tampered)
    assert cfg.gate_open("G_S21") is True  # the invariant predicate would now fail
    # And the shipped file itself still passes the invariant:
    assert load_config(_LIVE_JSON).gate_open("G_S21") is False
