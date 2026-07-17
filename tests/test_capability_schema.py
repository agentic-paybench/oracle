"""Tier-2 VCDM capability credentials: schema, no-ranking, P-256, no key leak (M5)."""

import base64
import json
import subprocess
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO = Path(__file__).resolve().parents[1]
CAP_DIR = REPO / "docs" / "site" / "capabilities"
SCHEMA = REPO / "schema" / "capability.schema.json"
DID_DOC = REPO / "docs" / "site" / ".well-known" / "did.json"

_FORBIDDEN = {"score", "rank", "recommendation"}


def _b64url(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


def _enveloped_files():
    return sorted(p for p in CAP_DIR.glob("*.vc.json"))


def _jwt_parts(vc_path: Path):
    env = json.loads(vc_path.read_text(encoding="utf-8"))
    assert env["type"] == "EnvelopedVerifiableCredential"
    jwt = env["id"].split("data:application/vc+jwt,", 1)[1]
    header_b64, payload_b64, _sig = jwt.split(".")
    header = json.loads(_b64url(header_b64))
    payload = json.loads(_b64url(payload_b64))
    return header, payload


def _deep_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _deep_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _deep_keys(v)


def test_capabilities_exist():
    files = _enveloped_files()
    assert files, "no signed capability VCs found (run the M5 signer)"


def test_capability_vc_validates_against_schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for f in _enveloped_files():
        _header, vc = _jwt_parts(f)
        jsonschema.validate(instance=vc, schema=schema)


def test_capability_vc_has_no_ranking_keys():
    for f in _enveloped_files():
        _header, vc = _jwt_parts(f)
        present = {k.lower() for k in _deep_keys(vc)} & _FORBIDDEN
        assert not present, f"{f.name} carries forbidden ranking key(s): {present}"


def test_signature_suite_is_p256_not_ed25519():
    doc = json.loads(DID_DOC.read_text(encoding="utf-8"))
    pub = doc["verificationMethod"][0]["publicKeyJwk"]
    assert pub["crv"] == "P-256"
    assert pub["kty"] == "EC"
    for f in _enveloped_files():
        header, _vc = _jwt_parts(f)
        assert header["alg"] == "ES256"  # ECDSA P-256
        assert header["alg"] not in ("EdDSA", "Ed25519")


def test_no_private_key_material_in_repo():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    # No private JWK or key files tracked; no dev-keys dir tracked.
    for path in tracked:
        assert not path.endswith(".jwk"), f"private JWK tracked: {path}"
        assert "/.dev-keys/" not in path, f"dev-keys tracked: {path}"
    # Published DID doc carries public key only (no JWK private component "d").
    doc = json.loads(DID_DOC.read_text(encoding="utf-8"))
    assert "d" not in doc["verificationMethod"][0]["publicKeyJwk"]
    # No PEM private blocks in tracked text. Needle is assembled at runtime so
    # this test's own source does not match; test sources are skipped anyway.
    pem_needle = "-----BEGIN " + "PRIVATE KEY"
    for path in tracked:
        if "/tests/" in path:
            continue
        fp = REPO / path
        try:
            text = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        assert pem_needle not in text, f"PEM private key in {path}"
