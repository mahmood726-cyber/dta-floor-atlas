# tests/test_engine_reitsma.py
from dta_floor_atlas.engines.reitsma import fit_reitsma
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_reitsma_returns_fit_result():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_reitsma(d, raise_on_error=False)
    assert fit.engine == "reitsma"


def test_reitsma_emits_auc_partial_when_converged():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_reitsma(d, raise_on_error=False)
    if fit.converged:
        assert fit.auc_partial is not None
        assert 0 < fit.auc_partial <= 1


def test_reitsma_failure_does_not_raise():
    d = _ds([(0, 5, 0, 50), (1, 4, 0, 50)])
    fit = fit_reitsma(d, raise_on_error=False)
    assert fit.engine == "reitsma"
