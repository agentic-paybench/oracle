"""public-manifest.toml default-deny check.

Every git-tracked file must appear in public-manifest.toml with a reason tag,
and every manifest entry must correspond to a tracked file. A tracked file
absent from the manifest fails CI: nothing reaches the public tree without a
declared reason for being public. Fail-closed in both directions.
"""

import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "public-manifest.toml"


def _manifest():
    with MANIFEST.open("rb") as f:
        return tomllib.load(f)


def _tracked():
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return {line for line in out.stdout.splitlines() if line}


def test_manifest_parses_and_declares_reasons():
    data = _manifest()
    assert set(data["reasons"]) == {"R0", "R1", "R2", "R3", "R4"}
    assert data["files"], "manifest has no file entries"


def test_every_tracked_file_has_a_reason():
    data = _manifest()
    missing = sorted(_tracked() - set(data["files"]))
    assert not missing, f"tracked files with no declared reason (default-deny): {missing}"


def test_every_manifest_entry_is_tracked():
    data = _manifest()
    stale = sorted(set(data["files"]) - _tracked())
    assert not stale, f"manifest entries with no tracked file: {stale}"


def test_every_tag_is_a_known_reason():
    data = _manifest()
    reasons = set(data["reasons"])
    bad = {f: tag for f, tag in data["files"].items() if tag not in reasons}
    assert not bad, f"unknown reason tags: {bad}"
