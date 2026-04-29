"""Floor 4 -- decision-flip rate (PRIMARY HEADLINE).

Grid-only after 2026-04-29 amendment (DTA70 lacks reported_prevalence).

Among datasets where >=2 primary comparators converge:
- pct_at_any_grid_prev: fraction with |delta PPV|>5pp or |delta NPV|>5pp at AT LEAST
  ONE prevalence in PREV_GRID = (0.01, 0.05, 0.20, 0.50)
- per_prev[p]: per-prevalence breakdown (auxiliary)

Strict inequality (>); 5pp exactly does NOT flag.
Differences rounded to 8 dp before comparison to avoid IEEE-754 boundary noise.
"""
from __future__ import annotations
from itertools import combinations
from dta_floor_atlas.types import FitResult
from dta_floor_atlas.thresholds import PPV_SWING, NPV_SWING, PREV_GRID
from dta_floor_atlas.prevalence import ppv_npv_swing


def compute_floor_4(
    fits_per_dataset: dict[str, list[FitResult]],
) -> dict:
    n_eligible = 0
    n_excluded = 0
    n_flagged_any = 0
    flagged_per_prev: dict[float, int] = {p: 0 for p in PREV_GRID}

    for dsid, fits in fits_per_dataset.items():
        converged = [f for f in fits if f.converged and f.pooled_se is not None]
        if len(converged) < 2:
            n_excluded += 1
            continue
        n_eligible += 1

        # For each prevalence anchor, check if any pairwise swing exceeds threshold.
        # Round swings to 8 dp to match Floor 3 boundary behaviour.
        flagged_at_any_grid_prev = False
        for prev in PREV_GRID:
            for a, b in combinations(converged, 2):
                swing = ppv_npv_swing(a.pooled_se, a.pooled_sp,
                                      b.pooled_se, b.pooled_sp, prev=prev)
                ppv_d = round(swing["ppv_swing"], 8)
                npv_d = round(swing["npv_swing"], 8)
                if ppv_d > PPV_SWING or npv_d > NPV_SWING:
                    flagged_per_prev[prev] += 1
                    flagged_at_any_grid_prev = True
                    break  # this dataset is flagged at this prevalence
        if flagged_at_any_grid_prev:
            n_flagged_any += 1

    pct_any = 100.0 * n_flagged_any / n_eligible if n_eligible > 0 else 0.0
    per_prev_pct = {
        p: {"n_flagged": flagged_per_prev[p],
            "pct": 100.0 * flagged_per_prev[p] / n_eligible if n_eligible > 0 else 0.0}
        for p in PREV_GRID
    }
    return {
        "pct_at_any_grid_prev": pct_any,
        "n_flagged": n_flagged_any,
        "n_eligible": n_eligible,
        "n_excluded": n_excluded,
        "per_prev": per_prev_pct,
    }
