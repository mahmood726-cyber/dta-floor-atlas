"""Pytest fixtures shared across all tests."""
from __future__ import annotations
import pytest

@pytest.fixture
def sample_2x2_table():
    """Minimal 2x2 contingency-table fixture for engine tests."""
    return [
        {"TP": 30, "FP": 5,  "FN": 2,  "TN": 60},
        {"TP": 45, "FP": 8,  "FN": 5,  "TN": 80},
        {"TP": 22, "FP": 3,  "FN": 1,  "TN": 50},
        {"TP": 55, "FP": 12, "FN": 8,  "TN": 95},
        {"TP": 38, "FP": 7,  "FN": 4,  "TN": 70},
    ]
