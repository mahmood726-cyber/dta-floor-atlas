"""Test Floor 4 -- decision-flip rate (grid-only per 2026-04-29 amendment)."""
from dta_floor_atlas.floors.decision_flip import compute_floor_4
from dta_floor_atlas.types import FitResult


def _fit(dsid, engine, se, sp, converged=True):
    return FitResult(
        dataset_id=dsid, engine=engine, cascade_level=1 if engine == "canonical" else "n/a",
        converged=converged, pooled_se=se if converged else None,
        pooled_sp=sp if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None, rho=None,
        tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0 if converged else 1,
        convergence_reason="ok" if converged else "non_convergence",
        raw_stdout_sha256=None,
    )


def test_floor_4_zero_when_methods_identical():
    fits = {"ds1": [
        _fit("ds1", "canonical", 0.85, 0.90),
        _fit("ds1", "copula", 0.85, 0.90),
        _fit("ds1", "reitsma", 0.85, 0.90),
        _fit("ds1", "moses", 0.85, 0.90),
    ]}
    floor = compute_floor_4(fits)
    assert floor["pct_at_any_grid_prev"] == 0.0


def test_floor_4_flagged_at_high_prevalence():
    """At 50% prevalence, large delta Se (15pp) produces >5pp NPV swing.

    Note: at low prevalence (1%), PPV swing from Se-only differences is small
    because FP rate (driven by Sp) dominates the PPV denominator. The NPV
    swing exceeds 5pp at high prevalence where diseased prevalence is large.
    Se 0.80 vs 0.95 with Sp=0.90 gives NPV swing ~12.9pp at prev=0.50.
    """
    fits = {"ds1": [
        _fit("ds1", "canonical", 0.80, 0.90),
        _fit("ds1", "copula", 0.95, 0.90),  # large delta Se; NPV at 50% prev will swing
        _fit("ds1", "reitsma", 0.80, 0.90),
        _fit("ds1", "moses", 0.80, 0.90),
    ]}
    floor = compute_floor_4(fits)
    # The 50% prevalence anchor should flag this (NPV swing ~12.9pp)
    assert floor["per_prev"][0.50]["pct"] > 0
    # any-grid pct should reflect the flag too
    assert floor["pct_at_any_grid_prev"] > 0


def test_floor_4_excludes_datasets_lt2_converged():
    fits = {"ds_too_few": [
        _fit("ds_too_few", "canonical", 0.85, 0.90),
        _fit("ds_too_few", "copula", None, None, converged=False),
        _fit("ds_too_few", "reitsma", None, None, converged=False),
        _fit("ds_too_few", "moses", None, None, converged=False),
    ]}
    floor = compute_floor_4(fits)
    assert floor["n_excluded"] == 1
    assert floor["n_eligible"] == 0
