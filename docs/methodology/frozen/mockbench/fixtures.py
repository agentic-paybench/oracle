"""Seeded log-normal fixture generation + content-addressing (methodology §6–§7).

A *fixture* is a content-addressed, calibrated population of finality-time
samples for one settling rail, drawn from that rail's empirical log-normal
``{median_s, sigma_log}`` (calibration provenance). The benchmark (``bench.py``)
draws trial outcomes from these fixtures; a trial records the fixture hash it
consumed (methodology §6).

Reproducibility contract (§5.4 item 6, §6):

* The master seed plus the rail id deterministically seed a stdlib Mersenne
  Twister stream — no wall-clock, no OS entropy.
* Samples are quantised to ``PRECISION_DECIMALS`` and serialised as fixed-format
  decimal strings, so the canonical bytes (and thus the sha256 content hash) are
  byte-stable and platform-independent.
* The content hash is computed over the fixture *payload* (everything except the
  hash field itself), then stored both in the fixture file and in the rail's
  provenance ``fixture_content_hash``.

Pure stdlib: ``random``, ``hashlib``, ``json``, ``math``, ``re``.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
from dataclasses import dataclass

from . import MASTER_SEED, N_FIXTURE_SAMPLES, PRECISION_DECIMALS
from .paths import FIXTURES_DIR, fixture_path, provenance_path

FIXTURE_SCHEMA = "paybench.fixture.v1"
GENERATOR_VERSION = "1"

# --- Provenance parsing (comment-preserving, no YAML dependency) -------------

_PARAMS_RE = re.compile(
    r"parameters:\s*\{\s*median_s:\s*([0-9.]+)\s*,\s*sigma_log:\s*([0-9.]+)\s*\}"
)
_RAIL_RE = re.compile(r'^rail:\s*"(.+?)"\s*$', re.MULTILINE)
_FAMILY_RE = re.compile(r"family:\s*([A-Za-z0-9_-]+)")
_HASH_LINE_RE = re.compile(r'^(fixture_content_hash:\s*)".*?"\s*$', re.MULTILINE)


@dataclass(frozen=True)
class RailCalibration:
    """The calibrated distribution for one rail, parsed from its provenance file.

    ``median_s`` and ``sigma_log`` are kept as the *literal source strings* (not
    floats) so the fixture content hash is coupled to the exact provenance values
    and carries zero float-formatting ambiguity.
    """

    rail_id: str
    rail_name: str
    family: str
    median_s: str
    sigma_log: str

    @property
    def mu(self) -> float:
        # log-normal: median = exp(mu)  ->  mu = ln(median_s)
        return math.log(float(self.median_s))

    @property
    def sigma(self) -> float:
        return float(self.sigma_log)


def load_calibration(rail_id: str) -> RailCalibration:
    text = provenance_path(rail_id).read_text(encoding="utf-8")
    pm = _PARAMS_RE.search(text)
    rm = _RAIL_RE.search(text)
    fm = _FAMILY_RE.search(text)
    if not pm or not rm or not fm:
        raise ValueError(f"could not parse calibration from provenance for {rail_id}")
    family = fm.group(1)
    if family != "lognormal":
        raise ValueError(
            f"{rail_id}: fixture generator only supports lognormal, got {family!r}"
        )
    return RailCalibration(
        rail_id=rail_id,
        rail_name=rm.group(1),
        family=family,
        median_s=pm.group(1),
        sigma_log=pm.group(2),
    )


# --- Deterministic seeding + sampling ----------------------------------------

def derive_seed(domain: str) -> int:
    """Domain-separated sub-seed from the single published master seed (§6)."""
    digest = hashlib.sha256(f"{MASTER_SEED}:{domain}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _format_sample(x: float) -> str:
    """Quantise to PRECISION_DECIMALS and format as a fixed-width decimal string.

    Fixed formatting (not float repr) is what makes the canonical bytes — and
    therefore the content hash — unambiguous across platforms/Python versions.
    """
    return f"{x:.{PRECISION_DECIMALS}f}"


def sample_finalities(cal: RailCalibration, n: int = N_FIXTURE_SAMPLES) -> list[str]:
    """Draw ``n`` seeded log-normal finality samples (as canonical strings)."""
    rng = random.Random(derive_seed(f"fixture:{cal.rail_id}"))
    mu, sigma = cal.mu, cal.sigma
    return [_format_sample(rng.lognormvariate(mu, sigma)) for _ in range(n)]


# --- Content addressing -------------------------------------------------------

def _canonical_bytes(payload: dict) -> bytes:
    """Canonical JSON bytes for hashing: sorted keys, no whitespace, ASCII."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def content_hash(payload: dict) -> str:
    """sha256 over the fixture payload (the hash field is never part of payload)."""
    return "sha256:" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def build_payload(cal: RailCalibration, samples: list[str]) -> dict:
    """The hashed content of a fixture: calibration + seed + the samples."""
    return {
        "schema": FIXTURE_SCHEMA,
        "rail_id": cal.rail_id,
        "rail_name": cal.rail_name,
        "dimension": "settlement-finality",
        "unit": "seconds",
        "distribution": {
            "family": cal.family,
            "median_s": cal.median_s,
            "sigma_log": cal.sigma_log,
        },
        "generator": {
            "name": "paybench-mockbench-fixture-gen",
            "version": GENERATOR_VERSION,
            "rng": "python-stdlib-random-mersenne-twister",
            "master_seed": MASTER_SEED,
            "rail_seed_domain": f"fixture:{cal.rail_id}",
            "rail_seed": derive_seed(f"fixture:{cal.rail_id}"),
        },
        "n_samples": len(samples),
        "precision_decimals": PRECISION_DECIMALS,
        "samples": samples,
    }


# --- Provenance write-back ----------------------------------------------------

def write_provenance_hash(rail_id: str, fixture_hash: str) -> bool:
    """Set ``fixture_content_hash`` in the rail's provenance file (idempotent).

    A surgical single-line substitution preserves all hand-written comments and
    formatting (no YAML round-trip). Returns True if the file changed.
    """
    path = provenance_path(rail_id)
    text = path.read_text(encoding="utf-8")
    new_text, n = _HASH_LINE_RE.subn(rf'\1"{fixture_hash}"', text)
    if n != 1:
        raise ValueError(
            f"{rail_id}: expected exactly one fixture_content_hash line, found {n}"
        )
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


# --- Top-level generation -----------------------------------------------------

@dataclass(frozen=True)
class GeneratedFixture:
    rail_id: str
    hash: str
    n_samples: int
    median_s: str
    sigma_log: str
    provenance_updated: bool


def generate_fixture(rail_id: str) -> GeneratedFixture:
    """Generate, content-address, persist one rail's fixture; write provenance."""
    cal = load_calibration(rail_id)
    samples = sample_finalities(cal)
    payload = build_payload(cal, samples)
    fh = content_hash(payload)

    # The fixture file = payload + its own content hash (recomputed over payload
    # only when verifying). Written with the same canonical encoder + a trailing
    # newline so the file bytes are themselves stable.
    out = dict(payload)
    out["content_hash"] = fh
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    fixture_path(rail_id).write_text(
        json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n",
        encoding="utf-8",
    )

    updated = write_provenance_hash(rail_id, fh)
    return GeneratedFixture(
        rail_id=rail_id,
        hash=fh,
        n_samples=len(samples),
        median_s=cal.median_s,
        sigma_log=cal.sigma_log,
        provenance_updated=updated,
    )


def load_fixture(rail_id: str) -> dict:
    """Load a generated fixture file and verify its content hash (integrity)."""
    obj = json.loads(fixture_path(rail_id).read_text(encoding="utf-8"))
    stored = obj.get("content_hash", "")
    payload = {k: v for k, v in obj.items() if k != "content_hash"}
    recomputed = content_hash(payload)
    if stored != recomputed:
        raise ValueError(
            f"{rail_id}: fixture content hash mismatch "
            f"(stored {stored}, recomputed {recomputed}) — fixture tampered or stale"
        )
    return obj


def fixture_samples_as_floats(rail_id: str) -> list[float]:
    """The fixture's finality samples as floats (for race draws / pass@k)."""
    return [float(s) for s in load_fixture(rail_id)["samples"]]
