"""pdp: the ADR-009 fail-closed canEmit Policy Decision Point.

Mechanic-aware, gate-keyed, wraps the ``RegulatoryGate``. The oracle owns the
shared regulatory_posture config at repo-root ``config/``.
"""

from pdp.config import ConfigError, PostureConfig, load_config, load_named
from pdp.gates import GATE_KEYS
from pdp.mechanics import EmitContext, MECHANICS, adr007_intent_free
from pdp.pdp import Decision, can_emit, evaluate

__all__ = [
    "ConfigError",
    "PostureConfig",
    "load_config",
    "load_named",
    "GATE_KEYS",
    "EmitContext",
    "MECHANICS",
    "adr007_intent_free",
    "Decision",
    "can_emit",
    "evaluate",
]
