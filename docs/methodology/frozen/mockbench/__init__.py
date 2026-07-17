"""PayBench N16 MockBench harness.

A unified, pure-stdlib Python harness for the settlement-finality benchmark
(methodology §5–§6). It does three things:

1. Generates seeded log-normal finality *fixtures* per settling rail from each
   rail's calibrated ``{median_s, sigma_log}`` (calibration provenance).
2. Content-addresses each fixture (sha256) and records the hash in the rail's
   provenance file (``fixture_content_hash``).
3. Runs the 5-rail → C(5,2)=10-pair → 5,000-trial finality benchmark and scores
   it with Bradley-Terry MLE + pass@k + Wilson lower-bound CIs.

Design constraints honoured (closed decisions):

* **N16 MockBench architecture** — unified Python harness in
  ``agentic-paybench/payhelm``; calibrated fixtures; content-addressed; seeded
  RNG; 500 trials/pair; finality races the 5 settling rails (AP2/R6 is on the
  Day-30 authorization-latency dimension per Resolution B, methodology §8).
* **N6 hybrid-tiered schema** — this harness measures the Tier-1 settlement-
  finality dimension only.
* **Reproducibility (§5.4 item 6, §6)** — a single published master seed drives
  all stochastic generation and ordering; fixtures are content-addressed; same
  seed + same fixtures → bit-for-bit reproducible run.

Pure standard library by design: zero third-party dependencies keeps the Day-0
artefact portable and removes cross-version RNG drift (stdlib ``random`` is the
version-stable Mersenne Twister). No numpy/scipy.
"""

from __future__ import annotations

# --- Pre-registered design constants (methodology §6) -----------------------

# A single published seed drives all stochastic fixture generation and trial
# ordering (methodology §6). Value = POC Day-0 date (2026-07-17) as an integer.
MASTER_SEED = 20260717

# The 5 settling rails that race on the Day-0 finality benchmark (§4; §8
# Resolution B excludes AP2/R6, which is measured on Day-30 authorization
# latency). Order is fixed and pre-registered.
SETTLING_RAILS = ["R1", "R2", "R9", "R10", "R11"]

# Per-rail fixture population size. Each rail appears in 4 pairs → 2,000 race
# draws; a 5,000-sample population comfortably covers that and gives a rich,
# content-addressed calibrated population for pass@k (§5.2).
N_FIXTURE_SAMPLES = 5000

# Decimal places at which generated finality samples are quantised before
# serialisation. Fixing this makes the canonical bytes — and therefore the
# content hash — unambiguous and platform-independent. 6 dp = microsecond
# precision on a seconds-valued measurement (far finer than any rail resolves).
PRECISION_DECIMALS = 6

# Trials per unordered rail pair (§6). 10 pairs × 500 = 5,000 total trials.
TRIALS_PER_PAIR = 500

# pass@k budgets in seconds (§5.2). Pre-registered grid chosen to span the
# calibrated medians (1.75s R10 … 16.52s R11): tight budgets separate the fast
# rails; wide budgets separate the slow ones.
K_GRID_SECONDS = [2, 3, 5, 10, 15, 20]

# z for a 95% two-sided Wilson interval (§5.3).
WILSON_Z_95 = 1.959963984540054

__all__ = [
    "MASTER_SEED",
    "SETTLING_RAILS",
    "N_FIXTURE_SAMPLES",
    "PRECISION_DECIMALS",
    "TRIALS_PER_PAIR",
    "K_GRID_SECONDS",
    "WILSON_Z_95",
]
