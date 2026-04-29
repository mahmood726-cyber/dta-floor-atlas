"""Moses-Littenberg D-vs-S linear regression.

Closed-form: regress D = logit(Se) - logit(1-Sp) on S = logit(Se) + logit(1-Sp).
Continuity correction (add 0.5 to all cells) ONLY when at least one cell is
zero — never unconditional, per advanced-stats.md.

Reference: Moses LE, Shapiro D, Littenberg B (1993). Stat Med 12:1293-1316.
"""
from __future__ import annotations
import math
import numpy as np
from dta_floor_atlas.types import Dataset, FitResult, StudyRow


def _continuity_corrected(row: StudyRow) -> tuple[float, float, float, float]:
    if 0 in (row.TP, row.FP, row.FN, row.TN):
        return row.TP + 0.5, row.FP + 0.5, row.FN + 0.5, row.TN + 0.5
    return float(row.TP), float(row.FP), float(row.FN), float(row.TN)


def _logit(p: float) -> float:
    p = max(1e-10, min(1.0 - 1e-10, p))
    return math.log(p / (1.0 - p))


def fit_moses(d: Dataset) -> FitResult:
    Ds, Ss = [], []
    for row in d.study_table:
        TP, FP, FN, TN = _continuity_corrected(row)
        se = TP / (TP + FN)
        sp = TN / (TN + FP)
        D = _logit(se) - _logit(1.0 - sp)
        S = _logit(se) + _logit(1.0 - sp)
        Ds.append(D)
        Ss.append(S)
    Ds, Ss = np.array(Ds), np.array(Ss)
    b = np.cov(Ds, Ss, ddof=1)[0, 1] / np.var(Ss, ddof=1)
    a = Ds.mean() - b * Ss.mean()
    S_pool = Ss.mean()
    D_pool = a + b * S_pool
    logit_se_pool = (S_pool + D_pool) / 2.0
    logit_one_minus_sp_pool = (S_pool - D_pool) / 2.0
    pooled_se = 1.0 / (1.0 + math.exp(-logit_se_pool))
    pooled_sp = 1.0 - 1.0 / (1.0 + math.exp(-logit_one_minus_sp_pool))

    return FitResult(
        dataset_id=d.dataset_id,
        engine="moses",
        cascade_level="n/a",
        converged=True,
        pooled_se=pooled_se,
        pooled_sp=pooled_sp,
        pooled_se_ci=None,
        pooled_sp_ci=None,
        rho=None,
        tau2_logit_se=None,
        tau2_logit_sp=None,
        auc_partial=None,
        r_version=None,
        package_version=None,
        call_string=f"moses(a={a:.6f}, b={b:.6f}, S_pool={S_pool:.6f})",
        exit_status=0,
        convergence_reason="ok",
        raw_stdout_sha256=None,
    )
