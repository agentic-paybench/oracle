"""Mechanic registry for the ADR-009 canEmit PDP.

Mechanic ids are stable descriptive slugs,
so ids stay unambiguous across integrator components. Each mechanic declares a
gate predicate, its ADR invariants, and whether it is posture-governed (subject to
the rail-liveness RegulatoryGate).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

from pdp.schema import RailRecord

# ADR-007 forbidden sets (both spellings of the asset-to-pay key).
_INTENT_PARAMS = {"amount", "payee", "asset-to-pay", "asset_to_pay"}
_FORBIDDEN_RESPONSE = {"score", "rank", "recommendation"}


@dataclass(frozen=True)
class EmitContext:
    """What a mechanic would emit, for invariant checking."""

    rails: Tuple[RailRecord, ...] = ()
    request_params: frozenset = frozenset()  # keys the query would accept
    response_keys: frozenset = frozenset()  # keys the response would carry


def adr007_intent_free(ctx: EmitContext) -> Tuple[bool, str]:
    """ADR-007: query rejects intent params; response strips score/rank/recommendation."""
    bad_req = _INTENT_PARAMS & set(ctx.request_params)
    if bad_req:
        return False, f"ADR-007: intent params present {sorted(bad_req)}"
    bad_resp = _FORBIDDEN_RESPONSE & set(ctx.response_keys)
    if bad_resp:
        return False, f"ADR-007: forbidden response keys {sorted(bad_resp)}"
    return True, "ADR-007 intent-free"


# --- gate predicates (config is duck-typed: .gate_open(key), .is_testnet()) ------

def _no_gate(cfg) -> bool:
    return True


def _requires_s21(cfg) -> bool:
    return cfg.gate_open("G_S21")


def _scored_9y(cfg) -> bool:
    # The scored query is testnet/demo only until G_AUTH (authorisation) or
    # G_QF (self-deploy) opens. G_S21 (financial promotion) does NOT unlock it,
    # so it is deliberately not consulted here.
    return cfg.is_testnet() or cfg.gate_open("G_AUTH") or cfg.gate_open("G_QF")


@dataclass(frozen=True)
class Mechanic:
    mechanic_id: str
    emission_class: str
    gate_predicate: Callable[[object], bool]
    invariants: Tuple[Callable[[EmitContext], Tuple[bool, str]], ...] = ()
    posture_governed: bool = False
    description: str = ""


MECHANICS = {
    m.mechanic_id: m
    for m in (
        Mechanic(
            "capability-read", "live", _no_gate,
            invariants=(adr007_intent_free,), posture_governed=False,
            description="Tier-2 factual capability read; ships live iff ADR-007 holds.",
        ),
        Mechanic(
            "finality-methodology", "live", _no_gate,
            description="Tier-1 settlement-finality methodology form; ships live, no ranking.",
        ),
        Mechanic(
            "published-rankings", "s21-gated", _requires_s21,
            description="Named-rail results table; G_S21-gated, default closed.",
        ),
        Mechanic(
            "scored-query", "posture-gated", _scored_9y, posture_governed=True,
            description="Scored/ranked query; testnet/demo only unless G_AUTH or G_QF opens.",
        ),
    )
}
