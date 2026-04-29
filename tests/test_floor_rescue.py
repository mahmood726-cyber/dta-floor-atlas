"""Test Floor 2 -- cascade spectrum (silent rescue + irreducible failure)."""
from dta_floor_atlas.floors.rescue import compute_floor_2
from dta_floor_atlas.types import FitResult


def _fit(dsid, level, converged=True):
    return FitResult(
        dataset_id=dsid, engine="canonical", cascade_level=level,
        converged=converged, pooled_se=None, pooled_sp=None,
        pooled_se_ci=None, pooled_sp_ci=None, rho=None,
        tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0 if converged else 1,
        convergence_reason="ok" if converged else "non_convergence",
        raw_stdout_sha256=None,
    )


def test_floor_2_pure_level_1():
    """All level 1 -> 0% rescue, 0% irreducible."""
    fits = [_fit(f"ds{i}", level=1) for i in range(76)]
    floor = compute_floor_2(fits, total_datasets=76)
    assert floor["floor_2a_pct"] == 0.0
    assert floor["floor_2b_pct"] == 0.0
    assert floor["floor_2c_pct"] == 0.0


def test_floor_2_decomposition_sums_to_floor_1():
    """Per spec invariant: Floor 1 = Floor 2a + Floor 2b + Floor 2c."""
    fits = (
        [_fit(f"l1_{i}", level=1) for i in range(60)]
        + [_fit(f"l2_{i}", level=2) for i in range(10)]
        + [_fit(f"l3_{i}", level=3) for i in range(4)]
        + [_fit(f"linf_{i}", level="inf", converged=False) for i in range(2)]
    )
    floor = compute_floor_2(fits, total_datasets=76)
    assert floor["floor_2a_pct"] == 100.0 * 10 / 76
    assert floor["floor_2b_pct"] == 100.0 * 4 / 76
    assert floor["floor_2c_pct"] == 100.0 * 2 / 76
    # Invariant
    floor_1_pct = 100.0 * (10 + 4 + 2) / 76
    decomp_sum = floor["floor_2a_pct"] + floor["floor_2b_pct"] + floor["floor_2c_pct"]
    assert abs(decomp_sum - floor_1_pct) < 1e-10
