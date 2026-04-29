"""Test Floor 3 -- inter-method disagreement at |delta Se|>5pp or |delta Sp|>5pp."""
from dta_floor_atlas.floors.disagreement import compute_floor_3
from dta_floor_atlas.types import FitResult


def _fit(dsid, engine, se, sp, converged=True):
    return FitResult(
        dataset_id=dsid, engine=engine, cascade_level=1 if engine == "canonical" else "n/a",
        converged=converged,
        pooled_se=se if converged else None,
        pooled_sp=sp if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0 if converged else 1,
        convergence_reason="ok" if converged else "non_convergence",
        raw_stdout_sha256=None,
    )


def test_floor_3_zero_when_all_methods_agree():
    """All 4 methods produce identical Se/Sp -> no disagreement."""
    fits_per_dataset = {
        "ds1": [
            _fit("ds1", "canonical", 0.85, 0.90),
            _fit("ds1", "copula", 0.85, 0.90),
            _fit("ds1", "reitsma", 0.85, 0.90),
            _fit("ds1", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits_per_dataset)
    assert floor["pct"] == 0.0
    assert floor["n_flagged"] == 0


def test_floor_3_flagged_when_pp_diff_exceeds_5pp():
    """delta Se = 6pp triggers flag (strict >5pp)."""
    fits = {
        "ds1": [
            _fit("ds1", "canonical", 0.85, 0.90),
            _fit("ds1", "copula", 0.91, 0.90),  # delta Se = 6pp
            _fit("ds1", "reitsma", 0.85, 0.90),
            _fit("ds1", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits)
    assert floor["n_flagged"] == 1
    assert floor["pct"] == 100.0


def test_floor_3_strict_inequality_at_exactly_5pp():
    """delta Se = 5pp exactly does NOT flag (per spec: strict >, not >=)."""
    fits = {
        "ds1": [
            _fit("ds1", "canonical", 0.85, 0.90),
            _fit("ds1", "copula", 0.90, 0.90),  # delta Se = 5pp exactly
            _fit("ds1", "reitsma", 0.85, 0.90),
            _fit("ds1", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits)
    assert floor["n_flagged"] == 0


def test_floor_3_excludes_datasets_with_lt2_converged():
    """Dataset with <2 converged comparators is excluded from Floor 3."""
    fits = {
        "ds_too_few": [
            _fit("ds_too_few", "canonical", 0.85, 0.90),
            _fit("ds_too_few", "copula", None, None, converged=False),
            _fit("ds_too_few", "reitsma", None, None, converged=False),
            _fit("ds_too_few", "moses", None, None, converged=False),
        ],
        "ds_ok": [
            _fit("ds_ok", "canonical", 0.85, 0.90),
            _fit("ds_ok", "copula", 0.85, 0.90),
            _fit("ds_ok", "reitsma", 0.85, 0.90),
            _fit("ds_ok", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits)
    assert floor["n_excluded"] == 1
    assert floor["n_eligible"] == 1
