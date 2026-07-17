"""ADR-007 Intent-Free Oracle: CI property test against the LIVE posture.

Proves the live oracle (1) refuses every intent param, (2) never emits a
score/rank/recommendation in any served credential, the schema, or under
injected-key fuzzing, and (3) keeps the scored query inert.
"""

import base64
import json
from pathlib import Path

from pdp import EmitContext, can_emit, load_named

REPO = Path(__file__).resolve().parents[1]
CAP_DIR = REPO / "docs" / "site" / "capabilities"
SCHEMA = REPO / "schema" / "capability.schema.json"

INTENT_PARAMS = ["amount", "payee", "asset-to-pay", "asset_to_pay"]
FORBIDDEN_RESPONSE = ["score", "rank", "recommendation"]


def _live():
    return load_named("live")


# --- (1) the query refuses intent params -------------------------------------

def test_live_read_refuses_each_intent_param():
    for param in INTENT_PARAMS:
        d = can_emit("capability-read", EmitContext(request_params=frozenset({param})), _live())
        assert not d.allowed, f"live read accepted intent param {param}"
        assert "ADR-007" in d.rationale


def test_live_read_allows_intent_free_query():
    ctx = EmitContext(request_params=frozenset({"rail_id"}), response_keys=frozenset({"fees"}))
    assert can_emit("capability-read", ctx, _live()).allowed


def test_live_read_refuses_each_forbidden_response_key():
    for key in FORBIDDEN_RESPONSE:
        d = can_emit("capability-read", EmitContext(response_keys=frozenset({key})), _live())
        assert not d.allowed


# --- (2) no served credential / the schema carries a ranking key --------------

def _b64url(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


def _payload(vc_path: Path) -> dict:
    env = json.loads(vc_path.read_text(encoding="utf-8"))
    jwt = env["id"].split("data:application/vc+jwt,", 1)[1]
    return json.loads(_b64url(jwt.split(".")[1]))


def _deep_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _deep_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _deep_keys(v)


def test_no_served_credential_carries_a_ranking_key():
    files = sorted(CAP_DIR.glob("*.vc.json"))
    assert files, "no served credentials to scan"
    for f in files:
        keys = {k.lower() for k in _deep_keys(_payload(f))}
        assert not (keys & set(FORBIDDEN_RESPONSE)), f"{f.name} carries a ranking key"


def test_schema_forbids_ranking_keys_structurally():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    subject = schema["properties"]["credentialSubject"]
    assert subject["additionalProperties"] is False
    for key in FORBIDDEN_RESPONSE:
        assert key not in subject["properties"]


# --- property/fuzz: any injected forbidden key is always caught ---------------

def test_fuzz_injected_intent_or_ranking_is_denied():
    live = _live()
    for bad in INTENT_PARAMS:
        ctx = EmitContext(request_params=frozenset({bad, "rail_id"}))
        assert not can_emit("capability-read", ctx, live).allowed
    for bad in FORBIDDEN_RESPONSE:
        ctx = EmitContext(response_keys=frozenset({bad, "fees"}))
        assert not can_emit("capability-read", ctx, live).allowed


# --- (3) the scored query is inert on the live oracle ------------------------

def test_scored_query_inert_on_live():
    assert not can_emit("scored-query", EmitContext(), _live()).allowed
