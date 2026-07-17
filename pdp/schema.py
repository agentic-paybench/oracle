"""Minimal capability + perimeter types for the Day-0 backbone.

Just what the canEmit PDP, the regulatory gate, and the Tier-2 capability builder
need: a rail's Tier-2 facts and a perimeter-liveness classification. Scoring and
ranking types are out of scope for this public capability oracle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DataClass(str, Enum):
    """Perimeter classification of a signal's measurement source.

    Load-bearing for the regulatory gate: only ``LIVE`` (a live mainnet
    measurement) can be a live-qualifying-cryptoasset emission target.
    """

    TESTNET = "testnet"
    DEVNET = "devnet"
    REGTEST = "regtest"
    FIRST_PARTY_NONLIVE = "first-party-nonlive"
    PLACEHOLDER = "placeholder"
    LIVE = "live"

    @property
    def is_live(self) -> bool:
        return self is DataClass.LIVE


@dataclass(frozen=True)
class RailFacts:
    """Tier-2 factual lookup for a rail. Unknown facts stay ``None`` (pending)."""

    rail_id: str
    name: str
    settles_independently: bool = True
    supported_assets: Optional[tuple[str, ...]] = None
    custody_model: Optional[str] = None
    headline_fee: Optional[str] = None


@dataclass(frozen=True)
class RailRecord:
    """A rail = its Tier-2 facts + the perimeter class of each measured signal.

    The measured values themselves (finality medians, ranks) are not carried on
    the public surface; only the perimeter class, which the gate reads.
    """

    facts: RailFacts
    signal_data_classes: tuple[DataClass, ...] = ()

    @property
    def rail_id(self) -> str:
        return self.facts.rail_id

    @property
    def is_live_qualifying_cryptoasset(self) -> bool:
        """Conservative: True if any signal is a live mainnet measurement."""
        return any(dc.is_live for dc in self.signal_data_classes)


@dataclass
class RailSpine:
    """A set of rails, keyed by rail id."""

    rails: dict[str, RailRecord] = field(default_factory=dict)

    def rail_ids(self) -> list[str]:
        return sorted(self.rails)
