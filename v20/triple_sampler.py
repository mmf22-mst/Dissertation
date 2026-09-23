"""
Stratified triple sampling and Wilson intervals — Paper 2 §5.1.

Entailment-verified precision is estimated on a stratified random sample
of n triples per KG (pinned; overview: n = 2,000), stratified by source
genre with proportional allocation, or every triple if the KG holds
fewer.  The sample is drawn with the S-HAR seed, recorded per KG.

Allocation is proportional with largest-remainder rounding, so strata
sizes sum to n exactly and small genres are not rounded to zero unless
they hold no triples.  Within a stratum the draw is a seeded shuffle of
the provenance records sorted by triple key, so it is reproducible from
(provenance, seed) alone.

Wilson score intervals are used for every proportion reported by the
population instruments (precision, sensitivity, specificity); they
behave at 0% and 100%, which matters for floor cells.

Dependencies: none beyond the standard library.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .kg_model import ProvenanceRecord

SAMPLE_N_DEFAULT = 2000   # the pinned value; recorded in the manifest


# ── Wilson interval ─────────────────────────────────────────────────


@dataclass(frozen=True)
class Proportion:
    successes: int
    trials: int
    estimate: float
    lower: float
    upper: float
    half_width: float

    def as_dict(self) -> Dict[str, float]:
        return {"successes": self.successes, "trials": self.trials, "estimate": self.estimate,
                "wilson_lower": self.lower, "wilson_upper": self.upper, "half_width": self.half_width}


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> Proportion:
    """Wilson score interval (95% by default)."""
    if trials <= 0:
        return Proportion(0, 0, float("nan"), float("nan"), float("nan"), float("nan"))
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    lower, upper = centre - half, centre + half
    # clamp, absorbing floating-point residue at the boundaries
    lower = 0.0 if lower < 1e-12 else lower
    upper = 1.0 if upper > 1 - 1e-12 else upper
    return Proportion(successes, trials, p, lower, upper, half)


# ── Allocation ──────────────────────────────────────────────────────


def proportional_allocation(counts: Dict[str, int], n: int) -> Dict[str, int]:
    """Largest-remainder proportional allocation of n across strata."""
    total = sum(counts.values())
    if total == 0:
        return {k: 0 for k in counts}
    if n >= total:
        return dict(counts)
    quotas = {k: n * c / total for k, c in counts.items()}
    alloc = {k: int(math.floor(q)) for k, q in quotas.items()}
    # cap by availability, then distribute the remainder by largest fractional part
    for k in alloc:
        alloc[k] = min(alloc[k], counts[k])
    remainder = n - sum(alloc.values())
    order = sorted(counts, key=lambda k: (-(quotas[k] - math.floor(quotas[k])), k))
    i = 0
    while remainder > 0 and order:
        k = order[i % len(order)]
        if alloc[k] < counts[k]:
            alloc[k] += 1
            remainder -= 1
        i += 1
        if i > 10 * len(order):
            break
    return alloc


# ── Sampling ────────────────────────────────────────────────────────


@dataclass
class TripleSample:
    records: List[ProvenanceRecord]
    allocation: Dict[str, int]
    population_by_genre: Dict[str, int]
    n_requested: int
    seed: int

    @property
    def n(self) -> int:
        return len(self.records)

    def as_dict(self) -> Dict[str, object]:
        return {"n_requested": self.n_requested, "n_drawn": self.n, "seed": self.seed,
                "allocation": self.allocation, "population_by_genre": self.population_by_genre}


def stratified_sample(provenance: Sequence[ProvenanceRecord], n: int, seed: int) -> TripleSample:
    """Proportional stratified sample by genre, seeded (S-HAR)."""
    by_genre: Dict[str, List[ProvenanceRecord]] = {}
    for r in provenance:
        by_genre.setdefault(r.genre, []).append(r)
    counts = {g: len(v) for g, v in sorted(by_genre.items())}
    alloc = proportional_allocation(counts, n)
    rng = random.Random(seed)
    chosen: List[ProvenanceRecord] = []
    for g in sorted(by_genre):
        pool = sorted(by_genre[g], key=lambda r: r.triple_key)
        k = alloc.get(g, 0)
        if k >= len(pool):
            chosen.extend(pool)
        else:
            idx = list(range(len(pool)))
            rng.shuffle(idx)
            chosen.extend(pool[i] for i in sorted(idx[:k]))
    return TripleSample(chosen, alloc, counts, n, seed)


def half_width_at(n: int, p: float = 0.8) -> float:
    """Planning helper: Wilson half-width at sample size n and precision p."""
    return wilson(round(n * p), n).half_width
