"""canEmit: the fail-closed ADR-009 Policy Decision Point.

Wraps (does not replace) the ``RegulatoryGate`` in :mod:`pdp.posture`.
A mechanic emits iff its gate predicate is satisfied AND its ADR invariants hold
AND (if posture-governed) the rail-liveness gate clears. Default deny.
"""

from __future__ import annotations

from dataclasses import dataclass

from pdp.posture import RegulatoryGate, RegulatoryGateError, Rung
from pdp.config import ConfigError, PostureConfig, load_named
from pdp.mechanics import EmitContext, MECHANICS


@dataclass(frozen=True)
class Decision:
    mechanic: str
    allowed: bool
    rationale: str

    def __bool__(self) -> bool:
        return self.allowed


def can_emit(mechanic_id: str, context: EmitContext, config: PostureConfig) -> Decision:
    mech = MECHANICS.get(mechanic_id)
    if mech is None:
        return Decision(mechanic_id, False, "unknown mechanic -> deny (fail-closed)")
    if not mech.gate_predicate(config):
        return Decision(
            mechanic_id, False,
            f"required gate(s) closed under config '{config.config_id}'",
        )
    for invariant in mech.invariants:
        ok, why = invariant(context)
        if not ok:
            return Decision(mechanic_id, False, f"invariant failed: {why}")
    if mech.posture_governed:
        gate = RegulatoryGate(
            posture=config.posture,
            authorised=config.gate_open("G_AUTH"),
            advised_out=config.gate_open("G_QF"),
        )
        try:
            gate.check(Rung.R0_INFORM, context.rails)
        except RegulatoryGateError as e:
            return Decision(mechanic_id, False, f"posture blocked: {e}")
    return Decision(mechanic_id, True, f"cleared under config '{config.config_id}'")


def evaluate(mechanic_id: str, context: EmitContext, config_name: str) -> Decision:
    """Load a named config and decide; fail-closed if the config is missing/bad."""
    try:
        config = load_named(config_name)
    except ConfigError as e:
        return Decision(mechanic_id, False, f"config load failed -> deny: {e}")
    return can_emit(mechanic_id, context, config)
