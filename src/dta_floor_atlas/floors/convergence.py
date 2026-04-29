"""Floor 1 -- canonical-bivariate convergence failure rate.

Numerator: count of datasets where canonical bivariate REML did NOT succeed
at cascade level 1 (i.e., level in {2, 3, 'inf'}).

Denominator: total DTA70 datasets (76 for v0.1).
"""
from __future__ import annotations
from typing import Iterable
from dta_floor_atlas.types import FitResult


def compute_floor_1(
    canonical_fits: Iterable[FitResult],
    total_datasets: int,
) -> dict:
    """Compute Floor 1 from a collection of canonical FitResults.

    canonical_fits: ONE per dataset, must be the cascade output (cascade_level
        attribute populated to 1, 2, 3, or 'inf').

    Returns:
        {n_failed, n_total, pct, by_level: {1: n, 2: n, 3: n, 'inf': n}}
    """
    by_level = {1: 0, 2: 0, 3: 0, "inf": 0}
    for f in canonical_fits:
        lvl = f.cascade_level
        if lvl in by_level:
            by_level[lvl] += 1
    n_at_level_1 = by_level[1]
    n_failed = total_datasets - n_at_level_1
    return {
        "n_failed": n_failed,
        "n_total": total_datasets,
        "pct": 100.0 * n_failed / total_datasets if total_datasets > 0 else 0.0,
        "by_level": by_level,
    }
