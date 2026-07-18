"""The ``regulatory_posture`` gate — load-bearing, do not soften.

- Draft **PERG 19.8** (the UK FCA's draft perimeter guidance) reads venue and
  price-finding expansively, so the gate applies the same precautionary test to
  every output tier, regardless of how any tier is ultimately classified —
  ``Rung`` only labels the tier, it never relaxes the gate.
- Emitting **any** tier against a live qualifying cryptoasset (SI 2026/102)
  requires an explicit clearance condition; the financial-promotion axis is
  separate. Default posture is the most restrictive.

Nothing reaches the outside world except through :meth:`RegulatoryGate.check`.
If an emission would breach the posture, it raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable

from pdp.schema import RailRecord


class Rung(IntEnum):
    """Output-tier label. Higher tiers are never more permitted; every tier
    passes the identical gate test. Only the inform-only tier is defined here;
    any future tier gates identically."""

    R0_INFORM = 0  # ranked comparison list (gated identically to every other tier)


class Posture(IntEnum):
    """The ``regulatory_posture`` flag. Default = most restrictive."""

    OFFLINE_TESTNET_ONLY = 0  # DEFAULT. Emit only against non-live first-party/testnet rails.
    FIRST_PARTY_DEMO = 1  # same perimeter as above; named separately for demo provenance.
    LIVE_AUTHORISED = 2  # emit against live qualifying cryptoassets — requires the clearance conditions below.


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
    authorised: bool = False  # FCA authorisation held for the relevant activity
    secondary_clearance: bool = False  # secondary clearance condition for the relevant activity

    def check(self, rung: Rung, rails: Iterable[RailRecord]) -> EmissionClearance:
        """Authorise (or refuse) emitting ``rung`` over ``rails``.

        Same precautionary test for every tier. The decision turns solely on
        whether any target rail is a *live qualifying cryptoasset* and whether
        the posture + clearance conditions permit that.
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
                    "cleared. The same precautionary test applies to every tier; none tripped here."
                ),
            )

        # At least one live qualifying cryptoasset target.
        if self.posture < Posture.LIVE_AUTHORISED:
            raise RegulatoryGateError(
                f"{rung.name} blocked: targets live qualifying cryptoasset(s) {list(live)} "
                f"under posture {self.posture.name} (need LIVE_AUTHORISED). The same "
                f"precautionary test applies to every tier. This deployment must not emit live."
            )
        if not (self.authorised or self.secondary_clearance):
            raise RegulatoryGateError(
                f"{rung.name} blocked: LIVE_AUTHORISED posture but neither FCA authorisation "
                f"nor the secondary clearance condition is set for live targets {list(live)}. "
                f"The gate requires an explicit clearance condition."
            )
        return EmissionClearance(
            rung=rung,
            posture=self.posture,
            rail_ids=rail_ids,
            live_qualifying=live,
            cleared=True,
            rationale=(
                f"{rung.name}: live targets {list(live)} cleared under LIVE_AUTHORISED "
                f"with {'authorisation' if self.authorised else 'clearance'}."
            ),
        )
