"""The two shared PDP gate configs are valid and default-closed (M3)."""

from pdp import GATE_KEYS, load_named


def test_configs_parse_and_validate():
    for name in ("testnet", "live"):
        cfg = load_named(name)
        assert set(cfg.gates) == set(GATE_KEYS)
        for value in cfg.gates.values():
            assert value in ("open", "closed")


def test_live_config_defaults_closed():
    cfg = load_named("live")
    # The three cross-to-live gates are closed on the live public oracle.
    assert cfg.gate_open("G_S21") is False
    assert cfg.gate_open("G_AUTH") is False
    assert cfg.gate_open("G_QF") is False
