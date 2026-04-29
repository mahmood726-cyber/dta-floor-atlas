"""Floor 3 -- inter-method disagreement at clinically meaningful threshold.

Among datasets where >=2 of {canonical, copula, reitsma, moses} converge,
fraction where max pairwise |delta Se| > 5pp OR |delta Sp| > 5pp.

Strict inequality (>); 5pp exactly does NOT flag.
"""
from __future__ import annotations
from itertools import combinations
from dta_floor_atlas.types import FitResult
from dta_floor_atlas.thresholds import SE_DELTA, SP_DELTA


def compute_floor_3(
    fits_per_dataset: dict[str, list[FitResult]],
) -> dict:
    """fits_per_dataset: {dataset_id: [FitResult, ...]} -- all 4 primary engines per dataset."""
    n_eligible = 0
    n_flagged = 0
    n_excluded = 0
    flagged_datasets = []

    for dsid, fits in fits_per_dataset.items():
        # Filter to converged primary fits only
        converged = [f for f in fits if f.converged and f.pooled_se is not None]
        if len(converged) < 2:
            n_excluded += 1
            continue
        n_eligible += 1
        # Compute max pairwise |Se| and |Sp| diff.
        # Round to 8 dp before comparison so that values that are exactly
        # SE_DELTA/SP_DELTA in decimal (e.g. 0.05) do not flag due to
        # IEEE-754 representation noise (0.90 - 0.85 = 0.05000...044).
        flagged = False
        for a, b in combinations(converged, 2):
            d_se = round(abs(a.pooled_se - b.pooled_se), 8)
            d_sp = round(abs(a.pooled_sp - b.pooled_sp), 8)
            if d_se > SE_DELTA or d_sp > SP_DELTA:
                flagged = True
                break
        if flagged:
            n_flagged += 1
            flagged_datasets.append(dsid)

    pct = 100.0 * n_flagged / n_eligible if n_eligible > 0 else 0.0
    return {
        "pct": pct,
        "n_flagged": n_flagged,
        "n_eligible": n_eligible,
        "n_excluded": n_excluded,
        "flagged_datasets": flagged_datasets,
    }
