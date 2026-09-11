"""The two shared PDP gate configs are valid; live opens only G_S21."""

from pdp import GATE_KEYS, load_named


def test_configs_parse_and_validate():
    for name in ("testnet", "live"):
        cfg = load_named(name)
        assert set(cfg.gates) == set(GATE_KEYS)
        for value in cfg.gates.values():
            assert value in ("open", "closed")


def test_live_config_gates():
    cfg = load_named("live")
    # G_S21 is open on the live public oracle: the named-rail measurement is
    # published. The gates that would unlock the scored query, and the reserved
    # custody gate, stay closed; G_S21 never shares a flag with them.
    assert cfg.gate_open("G_S21") is True
    assert cfg.gate_open("G_AUTH") is False
    assert cfg.gate_open("G_QF") is False
    assert cfg.gate_open("G_CUSTODY") is False
