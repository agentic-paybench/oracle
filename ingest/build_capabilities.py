"""Assemble Tier-2 RailCapability credentials from the de-ranked facts file (capability builder).

Reads ``ingest/data/rail-facts.json`` (Tier-2 facts only: railId, railName,
settlesIndependently; no finality medians or ranks), maps each to an intent-free
VCDM 2.0 credential subject, and writes one UNSIGNED VC per rail to
``ingest/build/capabilities/``. The Node signer (``ingest/signer/sign.mjs``) then
envelopes each as a VC-JOSE (ES256 / P-256).

Discipline: unknown facts (fees, supported assets, custody, the bundle) are
emitted as ``"pending"``, never invented. The schema forbids score/rank/
recommendation. The public build needs only the Tier-2 facts (no ranking data).

Tier-2 widening (October 2026): ``ingest/data/
rail-tier2-structural.json``, when present, adds documented structural cells
per rail (fee bearer, finality model class, retry and idempotency, ambiguity
bound, outcome knowledge, the restitution kind-table into
``bundle.refundSupport``, observer privacy exposure, specification pin,
declared rate limits, status page, SDK languages, error catalogue, offline
verifiability). Every cell
carries its own provenance. A subject that carries any structural cell also
carries the ``notice`` object, inside the signed credential, because a lookup
serves cells one rail at a time and a response has no "top". The ``measured`` label is refused here while the DIM-04 measured
annexes are held.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FACTS = REPO_ROOT / "ingest" / "data" / "rail-facts.json"
STRUCTURAL = REPO_ROOT / "ingest" / "data" / "rail-tier2-structural.json"
BUILD_DIR = REPO_ROOT / "ingest" / "build" / "capabilities"
DID_DOC = REPO_ROOT / "docs" / "site" / ".well-known" / "did.json"

# Deterministic Day-0 issuance instant (byte-stable outputs; no wall-clock).
VALID_FROM = "2026-07-17T00:00:00Z"
CONTEXT_URL = "https://oracle.agentic-paybench.dev/schema/capability.context.jsonld"
PLACEHOLDER_ISSUER = "did:jwk:PLACEHOLDER"


def _issuer() -> str:
    """The dev signing DID, if keygen has run; else a placeholder the signer fills."""
    if DID_DOC.is_file():
        return json.loads(DID_DOC.read_text(encoding="utf-8")).get("id", PLACEHOLDER_ISSUER)
    return PLACEHOLDER_ISSUER


# Pinned verbatim. The schema
# pins the same strings with "const", so a drift here fails validation.
DOCUMENTATION_STATEMENT = (
    "This is a documentation profile, not a recommendation: every cell states "
    "what a specification or an operator's own documentation says, no number in "
    "this document was produced by executing a payment, no rail is endorsed, no "
    "ordering implies a best buy, and no rail is being suggested for use."
)
SOURCES_STATEMENT = (
    "Every documentation-derived cell cites the primary source it rests on, by "
    "URL, with the date it was retrieved."
)
FIXED_ORDERING_STATEMENT = (
    "Rails are listed alphabetically by rail name. That ordering is fixed and "
    "carries no performance meaning."
)
# The fee-bearer variant (2026-10-09): the fee-adjacent cells quote fee
# documentation and carry no figures, so the figures-based fee-quotation sentence
# ("These figures are a quotation of a published fee schedule, ...") would be
# false here. That sentence stays pinned for any surface that carries figures.
FEE_QUOTATION_STATEMENT = (
    "These fee facts are a quotation of published fee documentation, not a "
    "recommendation: no rail is endorsed, no ordering implies a best buy, and no "
    "rail is being suggested for use."
)
FEE_EVEN_HANDED_STATEMENT = (
    "Every rail's fee facts are quoted from that rail's own published fee "
    "documentation, retrieved on the same date by the same procedure."
)

# The served statement page the notice points to (option C, ruled 2026-10-09).
STATEMENTS_URL = "https://oracle.agentic-paybench.dev/tier2/statements.md"
FEE_ADJACENT = {"feeBearer"}

STRUCTURAL_FIELDS = (
    "feeBearer", "finalityModelClass", "retryIdempotency", "ambiguityBound",
    "outcomeKnowledge", "observerPrivacyExposure", "specificationPin",
    "declaredRateLimits", "statusPage", "sdkLanguages", "errorCatalogue",
    "offlineVerifiability",
)


class MeasuredLabelRefused(ValueError):
    """A Tier-2 cell arrived labelled 'measured' while measured content is held."""


def notice(meta: dict) -> dict:
    """The notice object every structurally widened subject carries."""
    return {
        "kind": "documentation_profile",
        "profile": "level1-documentation-profile",
        "documentationStatement": DOCUMENTATION_STATEMENT,
        "sourcesStatement": SOURCES_STATEMENT,
        "fixedOrderingStatement": FIXED_ORDERING_STATEMENT,
        "evenHandedStatement": meta["evenHandedStatement"],
        "feeQuotation": {
            "kind": "fee_quotation",
            "appliesTo": ["fees", "feeBearer"],
            "quotationStatement": FEE_QUOTATION_STATEMENT,
            "sourceStatement": meta["feeSourceStatement"],
            "evenHandedStatement": FEE_EVEN_HANDED_STATEMENT,
            "statementsUrl": STATEMENTS_URL + "#fee-adjacent-cells-kind-fee_quotation",
        },
        "statementsUrl": STATEMENTS_URL,
    }


def _refuse_measured(rail_id: str, cells: dict) -> None:
    for name, cell in cells.items():
        if cell.get("provenance", {}).get("label") == "measured":
            raise MeasuredLabelRefused(
                f"{rail_id}.{name}: 'measured' is not permitted in Tier-2 while "
                "the DIM-04 measured annexes are held"
            )


def _load_structural() -> dict:
    if not STRUCTURAL.is_file():
        return {"meta": None, "rails": {}}
    data = json.loads(STRUCTURAL.read_text(encoding="utf-8"))
    return {"meta": data["meta"], "rails": {r["railId"]: r for r in data["rails"]}}


def capability_subject(rail: dict, structural: dict | None = None, meta: dict | None = None) -> dict:
    """Map a Tier-2 facts row to the Tier-2 credentialSubject. Unknowns -> "pending"."""
    subject = _base_subject(rail)
    if not structural:
        return subject
    cells = dict(structural.get("cells", {}))
    restitution = cells.pop("restitutionKinds", None)
    _refuse_measured(rail["railId"], cells | ({"restitutionKinds": restitution} if restitution else {}))
    subject["displayName"] = structural["displayName"]
    subject["notice"] = notice(meta)
    for name in STRUCTURAL_FIELDS:
        if name in cells:
            cell = dict(cells[name])
            cell["provenance"] = dict(cell["provenance"], profile="fee_quotation" if name in FEE_ADJACENT else "documentation_profile")
            subject[name] = cell
    if restitution:
        restitution = dict(restitution)
        restitution["provenance"] = dict(restitution["provenance"], profile="documentation_profile")
        subject["bundle"]["refundSupport"] = restitution
    return subject


def _base_subject(rail: dict) -> dict:
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


def unsigned_vc(rail: dict, issuer: str, structural: dict | None = None, meta: dict | None = None) -> dict:
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2", CONTEXT_URL],
        "type": ["VerifiableCredential", "RailCapabilityCredential"],
        "issuer": issuer,
        "validFrom": VALID_FROM,
        "credentialSubject": capability_subject(rail, structural, meta),
    }


def build() -> list[str]:
    rails = json.loads(FACTS.read_text(encoding="utf-8"))["rails"]
    issuer = _issuer()
    st = _load_structural()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for rail in sorted(rails, key=lambda r: r["railId"]):
        vc = unsigned_vc(rail, issuer, st["rails"].get(rail["railId"]), st["meta"])
        out = BUILD_DIR / f"{rail['railId']}.vc.json"
        out.write_text(json.dumps(vc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(rail["railId"])
    return written


if __name__ == "__main__":
    rails = build()
    print(f"built {len(rails)} unsigned capability VCs from rail-facts.json: {', '.join(rails)}")
