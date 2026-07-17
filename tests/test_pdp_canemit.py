"""ADR-009 canEmit PDP: fail-closed, gate-keyed, mechanic-aware (M3)."""

from dataclasses import replace

from pdp import EmitContext, can_emit, evaluate, load_named

INTENT_FREE = EmitContext(
    request_params=frozenset({"rail_id"}),
    response_keys=frozenset({"fees", "custodyModel"}),
)


def _live():
    return load_named("live")


def _testnet():
    return load_named("testnet")


def test_configs_load():
    assert _live().config_id == "live"
    assert _testnet().config_id == "testnet"


def test_unknown_mechanic_denied():
    d = can_emit("no-such-mechanic", INTENT_FREE, _live())
    assert not d.allowed and "unknown mechanic" in d.rationale


def test_unknown_gate_treated_closed():
    assert _live().gate_open("G_NONEXISTENT") is False  # fail-closed default


def test_default_config_denies_named_rail_table():
    for cfg in (_live(), _testnet()):
        d = can_emit("published-rankings", EmitContext(), cfg)
        assert not d.allowed  # G_S21 closed by default


def test_scored_query_inert_under_live():
    d = can_emit("scored-query", EmitContext(), _live())
    assert not d.allowed


def test_scored_query_works_under_testnet(spine):
    rails = tuple(spine.rails.values())
    d = can_emit("scored-query", EmitContext(rails=rails), _testnet())
    assert d.allowed, d.rationale


def test_s21_does_not_unlock_scored():
    cfg = _live()
    opened = replace(cfg, gates={**cfg.gates, "G_S21": "open"})
    d = can_emit("scored-query", EmitContext(), opened)
    assert not d.allowed  # s.21 must NOT unlock the scored query


def test_posture_does_not_unlock_named_table():
    # testnet (permissive for the demo) still cannot publish the named table.
    d = can_emit("published-rankings", EmitContext(), _testnet())
    assert not d.allowed


def test_tier2_read_allowed_under_live():
    d = can_emit("capability-read", INTENT_FREE, _live())
    assert d.allowed, d.rationale


def test_tier2_read_denied_when_intent_present():
    ctx = EmitContext(request_params=frozenset({"amount", "payee"}))
    d = can_emit("capability-read", ctx, _live())
    assert not d.allowed and "ADR-007" in d.rationale


def test_canemit_failclosed_on_missing_config(monkeypatch, tmp_path):
    monkeypatch.setenv("ORACLE_POSTURE_CONFIG", str(tmp_path))  # empty dir, no configs
    d = evaluate("capability-read", INTENT_FREE, "live")
    assert not d.allowed and "deny" in d.rationale.lower()
