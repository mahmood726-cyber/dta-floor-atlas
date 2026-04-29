"""Test the Strategy IV convergence cascade."""
from unittest.mock import patch
from dta_floor_atlas.engines.cascade import run_cascade
from dta_floor_atlas.types import Dataset, StudyRow, FitResult


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def _make_fit(converged: bool, level, reason: str = "ok") -> FitResult:
    return FitResult(
        dataset_id="test", engine="canonical", cascade_level=level,
        converged=converged,
        pooled_se=0.85 if converged else None, pooled_sp=0.90 if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=0.5 if converged else None,
        tau2_logit_se=0.1 if converged else None, tau2_logit_sp=0.1 if converged else None,
        auc_partial=None, r_version="R 4.5.2",
        package_version="metafor 4.6", call_string="rma.mv(...)",
        exit_status=0 if converged else 1,
        convergence_reason=reason,
        raw_stdout_sha256=None,
    )


def test_cascade_level_1_succeeds_on_first_try():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    with patch("dta_floor_atlas.engines.cascade._fit_at_level") as m:
        m.return_value = _make_fit(True, 1)
        result = run_cascade(d)
        assert result.cascade_level == 1
        assert result.converged is True
        assert m.call_count == 1


def test_cascade_falls_through_to_level_2():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fits = [_make_fit(False, 1, reason="non_convergence"), _make_fit(True, 2)]
    with patch("dta_floor_atlas.engines.cascade._fit_at_level", side_effect=fits) as m:
        result = run_cascade(d)
        assert result.cascade_level == 2
        assert result.converged is True
        assert m.call_count == 2


def test_cascade_falls_through_to_level_3():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fits = [_make_fit(False, 1, "non_convergence"),
            _make_fit(False, 2, "non_convergence"),
            _make_fit(True, 3)]
    with patch("dta_floor_atlas.engines.cascade._fit_at_level", side_effect=fits) as m:
        result = run_cascade(d)
        assert result.cascade_level == 3
        assert m.call_count == 3


def test_cascade_records_inf_on_irreducible_failure():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fits = [_make_fit(False, 1, "non_convergence"),
            _make_fit(False, 2, "non_convergence"),
            _make_fit(False, 3, "non_convergence")]
    with patch("dta_floor_atlas.engines.cascade._fit_at_level", side_effect=fits) as m:
        result = run_cascade(d)
        assert result.cascade_level == "inf"
        assert result.converged is False
        assert m.call_count == 3
