"""Pytest fixtures for the Day-0 backbone tests.

Synthetic, de-ranked spine: a handful of non-live rails carrying facts only (no
finality medians or ranks). The public backbone needs no ranking data to prove
the gates; a synthetic fixture suffices.
"""

import pytest

from pdp.schema import RailFacts, RailRecord, RailSpine


@pytest.fixture(scope="session")
def spine():
    rails = {
        rid: RailRecord(facts=RailFacts(rail_id=rid, name=f"{rid} (synthetic)"))
        for rid in ("R1", "R2", "R10")
    }
    return RailSpine(rails=rails)
