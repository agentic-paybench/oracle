"""The ``regulatory_posture`` gate — load-bearing, do not soften.

Encodes the session's regulatory guardrail directly:

- Draft **PERG 19.8** reads venue/price-finding + order-assistance as *likely
  arranging*. So R0 (a ranked advisory list) is **not** a safe harbour; the rungs
  are degrees of arranging *intensity*, not in-vs-out. The gate therefore applies
  the SAME test to every rung — ``Rung`` only labels intensity, it never relaxes
  the gate.
- The gate for emitting **any** rung on a live qualifying cryptoasset is
  *authorisation-or-advised-out*. Default posture is the most restrictive.
- This is the same perimeter axis as ``cryptoasset_perimeter_facts.md`` (SI
  2026/102; arranging regime commences 25 Oct 2027; s.21 financial-promotion is a
  separate, already-live axis since 8 Oct 2023).

The engine computes regardless; nothing reaches the outside world except through
:meth:`RegulatoryGate.check`. If a build step would emit live, it raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable

from pdp.schema import RailRecord


class Rung(IntEnum):
    """Axis A — arranging *intensity*. Higher = more arranging, NOT more permitted."""

    R0_INFORM = 0  # ranked advisory list (still likely arranging — PERG 19.8)
    R1_RECOMMEND = 1  # single best-rail pick
    R2_PREPARE = 2  # construct/pre-fill the executable instruction
    R3_ORCHESTRATE = 3  # delegated cross-rail routing + initiation (end-state)


class Posture(IntEnum):
    """The ``regulatory_posture`` flag. Default = most restrictive."""

    OFFLINE_TESTNET_ONLY = 0  # DEFAULT. Emit only against non-live first-party/testnet rails.
    FIRST_PARTY_DEMO = 1  # same perimeter as above; named separately for demo provenance.
    LIVE_AUTHORISED = 2  # emit against live qualifying cryptoassets — requires auth-or-advised-out.


class RegulatoryGateError(RuntimeError):
    """Raised when an emission would breach the posture. Surfacing, by design."""


@dataclass(frozen=True)
class EmissionClearance:
    rung: Rung
    posture: Posture
    rail_ids: tuple[str, ...]
    live_qualifying: tuple[str, ...]  # rails that ARE live qualifying cryptoassets (empty today)
    cleared: bool
    rationale: str


@dataclass
class RegulatoryGate:
    """The gate. Construct once; every emitter calls :meth:`check` before output."""

    posture: Posture = Posture.OFFLINE_TESTNET_ONLY  # most restrictive default
    authorised: bool = False  # FCA authorisation obtained for the arranging activity
    advised_out: bool = False  # qualified legal advice that the activity is out of scope

    def check(self, rung: Rung, rails: Iterable[RailRecord]) -> EmissionClearance:
        """Authorise (or refuse) emitting ``rung`` over ``rails``.

        Same test for every rung (PERG 19.8: even R0 is arranging). The decision
        turns solely on whether any target rail is a *live qualifying
        cryptoasset* and whether the posture + authorisation permit that.
        """
        rails = list(rails)
        rail_ids = tuple(r.rail_id for r in rails)
        live = tuple(r.rail_id for r in rails if r.is_live_qualifying_cryptoasset)

        if not live:
            # Nothing live-qualifying: emittable under any posture, all rungs.
            return EmissionClearance(
                rung=rung,
                posture=self.posture,
                rail_ids=rail_ids,
                live_qualifying=(),
                cleared=True,
                rationale=(
                    f"{rung.name}: no live qualifying cryptoasset in target set "
                    f"({len(rail_ids)} rail(s), all non-live testnet/first-party) — "
                    "cleared. PERG 19.8 applies equally to all rungs; none tripped here."
                ),
            )

        # At least one live qualifying cryptoasset target.
        if self.posture < Posture.LIVE_AUTHORISED:
            raise RegulatoryGateError(
                f"{rung.name} blocked: targets live qualifying cryptoasset(s) {list(live)} "
                f"under posture {self.posture.name} (need LIVE_AUTHORISED). PERG 19.8: even "
                f"R0 is arranging — no rung is a safe harbour. This session must not emit live."
            )
        if not (self.authorised or self.advised_out):
            raise RegulatoryGateError(
                f"{rung.name} blocked: LIVE_AUTHORISED posture but neither FCA authorisation "
                f"nor advised-out is set for live targets {list(live)}. Gate = "
                f"authorisation-or-advised-out."
            )
        return EmissionClearance(
            rung=rung,
            posture=self.posture,
            rail_ids=rail_ids,
            live_qualifying=live,
            cleared=True,
            rationale=(
                f"{rung.name}: live targets {list(live)} cleared under LIVE_AUTHORISED "
                f"with {'authorisation' if self.authorised else 'advised-out'}."
            ),
        )
