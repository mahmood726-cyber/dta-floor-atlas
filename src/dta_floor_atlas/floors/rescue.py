"""Floor 2 -- cascade spectrum.

Decomposes Floor 1 numerator into:
- Floor 2a: silent-rescue at level 2 (starting-value sweep)
- Floor 2b: silent-rescue at level 3 (rho fixed at 0)
- Floor 2c: irreducible failure (level inf)

Spec invariant: Floor 1 = Floor 2a + Floor 2b + Floor 2c (by construction).
"""
from __future__ import annotations
from typing import Iterable
from dta_floor_atlas.types import FitResult


def compute_floor_2(
    canonical_fits: Iterable[FitResult],
    total_datasets: int,
) -> dict:
    counts = {2: 0, 3: 0, "inf": 0}
    for f in canonical_fits:
        if f.cascade_level in counts:
            counts[f.cascade_level] += 1
    pct = lambda n: 100.0 * n / total_datasets if total_datasets > 0 else 0.0
    return {
        "floor_2a_pct": pct(counts[2]),
        "floor_2b_pct": pct(counts[3]),
        "floor_2c_pct": pct(counts["inf"]),
        "n_total": total_datasets,
        "counts_by_level": counts,
    }
