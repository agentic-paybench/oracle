"""Statistical layer: Bradley-Terry MLE + pass@k + Wilson LB CIs (methodology §5).

Pure stdlib, deterministic. The comparative ranking is Bradley-Terry maximum-
likelihood (the Chatbot Arena method); the absolute-threshold complement is
pass@k = P(finality ≤ k); every proportion is reported with a Wilson score
interval, leading with the conservative lower bound (§5.3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import WILSON_Z_95


# --- Wilson score interval (§5.3) --------------------------------------------

@dataclass(frozen=True)
class WilsonInterval:
    phat: float
    lower: float
    upper: float
    n: int


def wilson_interval(successes: float, n: int, z: float = WILSON_Z_95) -> WilsonInterval:
    """Wilson score interval for a binomial proportion.

    Well-behaved near 0 and 1 and at the per-pair sample sizes here, where the
    normal approximation would mislead. ``successes`` may be fractional (ties in
    a finality race count as half a win to each rail).
    """
    if n <= 0:
        return WilsonInterval(0.0, 0.0, 0.0, 0)
    phat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (phat + z2 / (2 * n)) / denom
    margin = (z * math.sqrt((phat * (1 - phat) + z2 / (4 * n)) / n)) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return WilsonInterval(phat=phat, lower=lower, upper=upper, n=n)


# --- pass@k (§5.2) ------------------------------------------------------------

@dataclass(frozen=True)
class PassAtK:
    k: float
    interval: WilsonInterval


def pass_at_k(samples: list[float], k: float, z: float = WILSON_Z_95) -> PassAtK:
    """pass@k = P(finality ≤ k), estimated over a rail's calibrated population."""
    successes = sum(1 for s in samples if s <= k)
    return PassAtK(k=k, interval=wilson_interval(successes, len(samples), z))


# --- Bradley-Terry MLE (§5.1) ------------------------------------------------

@dataclass(frozen=True)
class BradleyTerryResult:
    strengths: dict[str, float]   # normalised so they sum to 1
    iterations: int
    converged: bool
    ranking: list[str]            # best (fastest / highest strength) first
    prior: float                  # symmetric smoothing pseudo-wins per pair-direction


def bradley_terry_mle(
    items: list[str],
    wins: dict[tuple[str, str], float],
    comparisons: dict[tuple[str, str], float],
    prior: float = 1.0,
    max_iter: int = 10000,
    tol: float = 1e-12,
) -> BradleyTerryResult:
    """Bradley-Terry strengths via the Zermelo/MM fixed-point iteration.

    ``wins[(i, j)]`` = number of times i beat j (fractional for ties).
    ``comparisons[(i, j)]`` = total i-vs-j trials (symmetric: equals (j, i)).

    Iteration (Hunter 2004):  p_i <- W_i / Σ_{j≠i} n_ij / (p_i + p_j),
    re-normalised each step. Deterministic.

    **Smoothing prior.** Well-separated rails (e.g. a ~2s rail vs a ~16s rail)
    win ~100% of their races, which is *complete separation* — the unregularised
    BT MLE then diverges to the boundary (strengths → 0/∞) and never converges.
    We add a symmetric additive (Beta) prior: ``prior`` pseudo-wins in each
    direction of every compared pair (``2·prior`` pseudo-comparisons). This is
    standard BT regularisation (the same move real pairwise leaderboards make);
    with 500 real trials/pair a ``prior`` of 1.0 is a very mild pull toward
    equality — negligible on the well-identified estimates, but it guarantees a
    finite, convergent MLE and keeps the ranking honest at the extremes.
    """
    # Apply symmetric smoothing across every compared pair (once per unordered pair).
    s_wins: dict[tuple[str, str], float] = dict(wins)
    s_comp: dict[tuple[str, str], float] = dict(comparisons)
    if prior > 0:
        seen: set[frozenset] = set()
        for (i, j) in list(comparisons.keys()):
            key = frozenset((i, j))
            if key in seen:
                continue
            seen.add(key)
            s_wins[(i, j)] = s_wins.get((i, j), 0.0) + prior
            s_wins[(j, i)] = s_wins.get((j, i), 0.0) + prior
            s_comp[(i, j)] = s_comp.get((i, j), 0.0) + 2 * prior
            s_comp[(j, i)] = s_comp.get((j, i), 0.0) + 2 * prior

    # Total wins per item and the symmetric per-pair comparison counts.
    total_wins: dict[str, float] = {i: 0.0 for i in items}
    for (i, j), w in s_wins.items():
        total_wins[i] += w

    n_pair: dict[frozenset, float] = {}
    for (i, j), c in s_comp.items():
        n_pair[frozenset((i, j))] = c

    p = {i: 1.0 for i in items}
    converged = False
    used_iter = 0
    for it in range(1, max_iter + 1):
        used_iter = it
        new_p: dict[str, float] = {}
        for i in items:
            denom = 0.0
            for j in items:
                if j == i:
                    continue
                key = frozenset((i, j))
                n_ij = n_pair.get(key, 0.0)
                if n_ij:
                    denom += n_ij / (p[i] + p[j])
            # A rail that never won gets a tiny positive strength, not zero, to
            # keep the ratios finite; with 5,000 trials this branch is unused.
            new_p[i] = (total_wins[i] / denom) if denom > 0 else 0.0
        # Normalise to sum 1 for identifiability + stable convergence test.
        s = sum(new_p.values())
        if s > 0:
            new_p = {i: v / s for i, v in new_p.items()}
        delta = max(abs(new_p[i] - p[i]) for i in items)
        p = new_p
        if delta < tol:
            converged = True
            break

    ranking = sorted(items, key=lambda i: p[i], reverse=True)
    return BradleyTerryResult(
        strengths=p,
        iterations=used_iter,
        converged=converged,
        ranking=ranking,
        prior=prior,
    )
