"""MockBench settlement-finality harness (methodology §5–§6, §8 Resolution B).

Wires the calibrated, content-addressed fixtures into the pre-registered
experimental design:

* 5 settling rails → C(5,2) = **10 unordered pairs**
* **500 trials per pair → 5,000 total trials** (symmetric, fix-list item 3)
* a single published master seed drives every trial draw (§6)
* each trial is a finality *race*: draw one finality sample for each rail in the
  pair from its fixture population; the lower finality wins (ties split 0.5/0.5)
* scored with Bradley-Terry MLE + pass@k + Wilson lower-bound CIs (§5)

The run is deterministic: same seed + same fixtures → byte-identical report
(no wall-clock is written into the report), demonstrating §5.4 item 6.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from dataclasses import dataclass

from . import (
    K_GRID_SECONDS,
    MASTER_SEED,
    SETTLING_RAILS,
    TRIALS_PER_PAIR,
)
from .fixtures import derive_seed, load_fixture
from .paths import RUNS_DIR
from .stats import bradley_terry_mle, pass_at_k, wilson_interval


@dataclass(frozen=True)
class PairResult:
    a: str
    b: str
    trials: int
    wins_a: float
    wins_b: float
    ties: int


def race_pair(a: str, b: str, samples: dict[str, list[float]]) -> PairResult:
    """Run TRIALS_PER_PAIR seeded finality races between rails a and b.

    Per-pair RNG is domain-separated from the single master seed so pair order
    is irrelevant to any pair's outcome (a race is reproducible in isolation).
    """
    rng = random.Random(derive_seed(f"pair:{a}:{b}"))
    sa, sb = samples[a], samples[b]
    na, nb = len(sa), len(sb)
    wins_a = wins_b = 0.0
    ties = 0
    for _ in range(TRIALS_PER_PAIR):
        fa = sa[rng.randrange(na)]
        fb = sb[rng.randrange(nb)]
        if fa < fb:
            wins_a += 1
        elif fb < fa:
            wins_b += 1
        else:
            wins_a += 0.5
            wins_b += 0.5
            ties += 1
    return PairResult(a=a, b=b, trials=TRIALS_PER_PAIR, wins_a=wins_a, wins_b=wins_b, ties=ties)


def _run_hash(report_without_hash: dict) -> str:
    canon = json.dumps(
        report_without_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canon).hexdigest()


def run_benchmark(rails: list[str] = SETTLING_RAILS) -> dict:
    """Execute the full settlement-finality benchmark and return the report dict.

    Loading each fixture verifies its content hash (the trial design records and
    re-checks the exact fixture bytes it consumes — content-addressing wired into
    the run, §6).
    """
    rails = list(rails)
    fixtures = {r: load_fixture(r) for r in rails}
    samples = {r: [float(s) for s in fixtures[r]["samples"]] for r in rails}

    pairs = [tuple(sorted(p)) for p in itertools.combinations(sorted(rails), 2)]

    # --- run every pair ---
    pair_results = [race_pair(a, b, samples) for (a, b) in pairs]

    # --- Bradley-Terry inputs ---
    wins: dict[tuple[str, str], float] = {}
    comparisons: dict[tuple[str, str], float] = {}
    for pr in pair_results:
        wins[(pr.a, pr.b)] = wins.get((pr.a, pr.b), 0.0) + pr.wins_a
        wins[(pr.b, pr.a)] = wins.get((pr.b, pr.a), 0.0) + pr.wins_b
        comparisons[(pr.a, pr.b)] = pr.trials
        comparisons[(pr.b, pr.a)] = pr.trials

    bt = bradley_terry_mle(rails, wins, comparisons)

    # --- per-pair win rates with Wilson LB (both directions) ---
    pair_report = []
    for pr in pair_results:
        ci_a = wilson_interval(pr.wins_a, pr.trials)
        ci_b = wilson_interval(pr.wins_b, pr.trials)
        pair_report.append(
            {
                "pair": [pr.a, pr.b],
                "trials": pr.trials,
                "wins": {pr.a: pr.wins_a, pr.b: pr.wins_b},
                "ties": pr.ties,
                "win_rate": {
                    pr.a: {
                        "phat": ci_a.phat,
                        "wilson_lb": ci_a.lower,
                        "wilson_ub": ci_a.upper,
                    },
                    pr.b: {
                        "phat": ci_b.phat,
                        "wilson_lb": ci_b.lower,
                        "wilson_ub": ci_b.upper,
                    },
                },
            }
        )

    # --- pass@k per rail over its calibrated population, with Wilson LB ---
    passk_report = {}
    for r in rails:
        rows = []
        for k in K_GRID_SECONDS:
            pk = pass_at_k(samples[r], k)
            rows.append(
                {
                    "k_seconds": k,
                    "phat": pk.interval.phat,
                    "wilson_lb": pk.interval.lower,
                    "wilson_ub": pk.interval.upper,
                    "n": pk.interval.n,
                }
            )
        passk_report[r] = rows

    report = {
        "schema": "paybench.finality-run.v1",
        "dimension": "settlement-finality",
        "config": {
            "master_seed": MASTER_SEED,
            "rails": rails,
            "rail_names": {r: fixtures[r]["rail_name"] for r in rails},
            "pairs": [list(p) for p in pairs],
            "n_pairs": len(pairs),
            "trials_per_pair": TRIALS_PER_PAIR,
            "total_trials": TRIALS_PER_PAIR * len(pairs),
            "k_grid_seconds": K_GRID_SECONDS,
            "fixture_hashes": {r: fixtures[r]["content_hash"] for r in rails},
        },
        "bradley_terry": {
            "strengths": bt.strengths,
            "ranking": bt.ranking,
            "iterations": bt.iterations,
            "converged": bt.converged,
            "smoothing_prior": bt.prior,
        },
        "pairs": pair_report,
        "pass_at_k": passk_report,
    }
    report["run_hash"] = _run_hash(report)
    return report


def write_report(report: dict) -> str:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / "finality-run.json"
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return str(out)
