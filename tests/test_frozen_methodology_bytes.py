"""Vendored frozen v1.2 public subset: byte-identical to anchor, ranking withheld."""

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FROZEN = REPO / "docs" / "methodology" / "frozen"
MANIFEST = FROZEN / "prereg-manifest.sha256"
ANCHOR = "a5f6feb46819dc3926012a8a38ac519cd0d5df33c20734516dca4b32d30d3a6f"
WITHHELD = "runs/finality-run.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_entries():
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, path = line.split(None, 1)
        yield digest, path.strip()


def test_manifest_selfhash_matches_anchor():
    assert _sha256(MANIFEST) == ANCHOR


def test_public_subset_matches_manifest_hashes():
    checked = 0
    for digest, path in _manifest_entries():
        if path == WITHHELD:
            continue
        f = FROZEN / path
        assert f.is_file(), f"missing vendored file {path}"
        assert _sha256(f) == digest, f"byte mismatch: {path}"
        checked += 1
    assert checked == 18, f"expected 18 public-subset files, checked {checked}"


def test_ranking_artefacts_absent():
    assert not (FROZEN / WITHHELD).is_file()
    docs = REPO / "docs"
    for p in docs.rglob("*"):
        name = p.name.lower()
        assert "finality-run" not in name, f"ranking artefact present: {p}"
        assert "name-map" not in name and "name_map" not in name, f"name map present: {p}"
