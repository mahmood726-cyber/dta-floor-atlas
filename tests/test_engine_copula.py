# tests/test_engine_copula.py
import pytest
from dta_floor_atlas.engines.copula import fit_copula
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_copula_returns_fit_result():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_copula(d, raise_on_error=False)
    assert fit.engine == "copula"
    assert fit.dataset_id == "test"


def test_copula_records_r_audit_fields():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_copula(d, raise_on_error=False)
    assert fit.r_version is not None
    assert fit.call_string is not None and "CopulaREMADA" in fit.call_string


def test_copula_failure_does_not_raise():
    d = _ds([(0, 5, 0, 50), (1, 4, 0, 50)])
    fit = fit_copula(d, raise_on_error=False)
    assert fit.engine == "copula"
