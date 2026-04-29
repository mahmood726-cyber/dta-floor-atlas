import pytest
from dta_floor_atlas.engines.canonical import fit_canonical
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_canonical_returns_fit_result():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_canonical(d)
    assert fit.engine == "canonical"
    assert fit.dataset_id == "test"


def test_canonical_records_r_call_audit():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_canonical(d)
    assert fit.r_version is not None
    assert fit.call_string is not None and "rma.mv" in fit.call_string


def test_canonical_returns_se_sp_in_unit_interval_when_converged():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_canonical(d)
    if fit.converged:
        assert 0 < fit.pooled_se < 1
        assert 0 < fit.pooled_sp < 1


def test_canonical_records_failure_without_raising_when_raise_disabled():
    """A pathological dataset (k=2, all-zero in one arm) should record failure,
    not crash, when raise_on_error=False."""
    d = _ds([(0, 5, 0, 50), (1, 4, 0, 50)])
    fit = fit_canonical(d, raise_on_error=False)
    assert fit.engine == "canonical"
    assert fit.exit_status in (0, 1)
