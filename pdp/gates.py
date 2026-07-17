"""Gate keys for the ADR-009 canEmit PDP. Unknown gate = closed (fail-closed)."""

from __future__ import annotations

# The four regulatory gates keyed in the regulatory_posture config (ADR-009).
GATE_KEYS = ("G_AUTH", "G_QF", "G_S21", "G_CUSTODY")

OPEN = "open"
CLOSED = "closed"


def is_open(gates: dict, key: str) -> bool:
    """A gate is open only if explicitly set to "open"; unknown/missing = closed."""
    return gates.get(key) == OPEN
