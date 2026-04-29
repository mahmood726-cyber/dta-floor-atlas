"""Test Floor 1 -- canonical-bivariate convergence failure rate."""
import pytest
from dta_floor_atlas.floors.convergence import compute_floor_1
from dta_floor_atlas.types import FitResult


def _fit(dataset_id, level, converged=True):
    return FitResult(
        dataset_id=dataset_id, engine="canonical", cascade_level=level,
        converged=converged,
        pooled_se=0.85 if converged else None,
        pooled_sp=0.90 if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=0.5, tau2_logit_se=0.1, tau2_logit_sp=0.1, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
    )


def test_floor_1_zero_when_all_at_level_1():
    """All canonical fits succeed at level 1 -> Floor 1 = 0%."""
    fits = [_fit(f"ds{i}", level=1) for i in range(76)]
    floor = compute_floor_1(fits, total_datasets=76)
    assert floor["pct"] == 0.0
    assert floor["n_failed"] == 0
    assert floor["n_total"] == 76


def test_floor_1_50pct_when_half_at_level_1():
    fits_l1 = [_fit(f"ds{i}", level=1) for i in range(38)]
    fits_l2 = [_fit(f"ds{i+38}", level=2) for i in range(38)]
    floor = compute_floor_1(fits_l1 + fits_l2, total_datasets=76)
    assert floor["n_failed"] == 38
    assert abs(floor["pct"] - 50.0) < 1e-10


def test_floor_1_includes_inf_failures():
    """Level inf (irreducible failure) counts as Floor 1 failure too."""
    fits = [_fit("ds0", level=1)] * 75
    fits.append(_fit("ds_fail", level="inf", converged=False))
    floor = compute_floor_1(fits, total_datasets=76)
    assert floor["n_failed"] == 1
