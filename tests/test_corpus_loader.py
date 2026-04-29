"""Test DTA70 corpus loader."""
import pytest
from dta_floor_atlas.corpus.loader import load_dta70_datasets
from dta_floor_atlas.types import Dataset, StudyRow


def test_loader_emits_76_datasets():
    datasets = list(load_dta70_datasets())
    assert len(datasets) == 76, f"DTA70 v0.1.0 has 76 datasets; got {len(datasets)}"


def test_each_dataset_has_required_fields():
    datasets = list(load_dta70_datasets())
    for d in datasets:
        assert isinstance(d, Dataset)
        assert d.dataset_id and isinstance(d.dataset_id, str)
        assert d.n_studies > 0
        assert len(d.study_table) == d.n_studies
        for row in d.study_table:
            assert isinstance(row, StudyRow)
            assert row.TP >= 0 and row.FP >= 0 and row.FN >= 0 and row.TN >= 0


def test_total_studies_at_least_1966():
    """DTA70 v0.1.0 has 1,966+ studies across all datasets."""
    datasets = list(load_dta70_datasets())
    total = sum(d.n_studies for d in datasets)
    assert total >= 1966, f"DTA70 should have >=1966 studies; got {total}"


def test_reported_prevalence_optional_but_typed():
    datasets = list(load_dta70_datasets())
    for d in datasets:
        if d.reported_prevalence is not None:
            assert 0.0 < d.reported_prevalence < 1.0
