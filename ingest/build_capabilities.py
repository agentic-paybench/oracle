"""Assemble Tier-2 RailCapability credentials from the de-ranked facts file (M5).

Reads ``ingest/data/rail-facts.json`` (Tier-2 facts only: railId, railName,
settlesIndependently; no finality medians or ranks), maps each to an intent-free
VCDM 2.0 credential subject, and writes one UNSIGNED VC per rail to
``ingest/build/capabilities/``. The Node signer (``ingest/signer/sign.mjs``) then
envelopes each as a VC-JOSE (ES256 / P-256).

Discipline: unknown facts (fees, supported assets, custody, the bundle) are
emitted as ``"pending"``, never invented. The schema forbids score/rank/
recommendation. The public build needs only the Tier-2 facts (no ranking data).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FACTS = REPO_ROOT / "ingest" / "data" / "rail-facts.json"
BUILD_DIR = REPO_ROOT / "ingest" / "build" / "capabilities"
DID_DOC = REPO_ROOT / "docs" / "site" / ".well-known" / "did.json"

# Deterministic Day-0 issuance instant (byte-stable outputs; no wall-clock).
VALID_FROM = "2026-07-17T00:00:00Z"
CONTEXT_URL = "https://agentic-paybench.example/schema/capability.context.jsonld"
PLACEHOLDER_ISSUER = "did:jwk:PLACEHOLDER"


def _issuer() -> str:
    """The dev signing DID, if keygen has run; else a placeholder the signer fills."""
    if DID_DOC.is_file():
        return json.loads(DID_DOC.read_text(encoding="utf-8")).get("id", PLACEHOLDER_ISSUER)
    return PLACEHOLDER_ISSUER


def capability_subject(rail: dict) -> dict:
    """Map a Tier-2 facts row to the N6 Tier-2 credentialSubject. Unknowns -> "pending"."""
    return {
        "id": f"urn:agentic-paybench:rail:{rail['railId']}",
        "railId": rail["railId"],
        "railName": rail["railName"],
        "settlesIndependently": rail["settlesIndependently"],
        "fees": {"model": "pending", "headlineFee": "pending"},
        "supportedAssets": "pending",
        "custodyModel": "pending",
        "bundle": {
            "authorizationModel": "pending",
            "disputeMechanism": "pending",
            "refundSupport": "pending",
            "sanctionsScreening": "pending",
        },
    }


def unsigned_vc(rail: dict, issuer: str) -> dict:
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2", CONTEXT_URL],
        "type": ["VerifiableCredential", "RailCapabilityCredential"],
        "issuer": issuer,
        "validFrom": VALID_FROM,
        "credentialSubject": capability_subject(rail),
    }


def build() -> list[str]:
    rails = json.loads(FACTS.read_text(encoding="utf-8"))["rails"]
    issuer = _issuer()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for rail in sorted(rails, key=lambda r: r["railId"]):
        vc = unsigned_vc(rail, issuer)
        out = BUILD_DIR / f"{rail['railId']}.vc.json"
        out.write_text(json.dumps(vc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(rail["railId"])
    return written


if __name__ == "__main__":
    rails = build()
    print(f"built {len(rails)} unsigned capability VCs from rail-facts.json: {', '.join(rails)}")
