"""Filesystem layout for the MockBench harness.

All paths are resolved relative to this file so the harness is runnable from any
working directory (``python -m paybench.mockbench.cli ...`` from the repo root,
or directly).
"""

from __future__ import annotations

from pathlib import Path

# .../paybench/mockbench/paths.py -> .../paybench
PAYBENCH_DIR = Path(__file__).resolve().parents[1]

CALIBRATION_DIR = PAYBENCH_DIR / "calibration"
PROVENANCE_DIR = CALIBRATION_DIR / "provenance"
SAMPLES_DIR = CALIBRATION_DIR / "samples"

# Generated, committable artefacts (note: *.json is NOT gitignored; *.jsonl is).
FIXTURES_DIR = PAYBENCH_DIR / "fixtures"
RUNS_DIR = PAYBENCH_DIR / "runs"

# Rail id -> calibration provenance filename (settlement-finality batch).
RAIL_PROVENANCE = {
    "R1": "R1-x402-base-finality.provenance.yaml",
    "R2": "R2-x402-stellar-finality.provenance.yaml",
    "R9": "R9-x402-solana-finality.provenance.yaml",
    "R10": "R10-mpp-tempo-finality.provenance.yaml",
    "R11": "R11-mpp-lightning-finality.provenance.yaml",
}


def provenance_path(rail_id: str) -> Path:
    return PROVENANCE_DIR / RAIL_PROVENANCE[rail_id]


def fixture_path(rail_id: str) -> Path:
    return FIXTURES_DIR / f"{rail_id}-finality.fixture.json"
