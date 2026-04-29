"""Shared helpers for R-backed engines: continuity-correction logic + study-table
JSON serialization for env-var injection."""
from __future__ import annotations
import json
from dta_floor_atlas.types import Dataset, StudyRow


def study_table_to_r_json(study_table: tuple[StudyRow, ...]) -> str:
    """Serialize study table to JSON consumable by R fromJSON()."""
    return json.dumps([
        {"TP": r.TP, "FP": r.FP, "FN": r.FN, "TN": r.TN}
        for r in study_table
    ])


def needs_continuity(study_table: tuple[StudyRow, ...]) -> bool:
    """True if any study has a zero cell (per advanced-stats.md: only then add 0.5)."""
    return any(0 in (r.TP, r.FP, r.FN, r.TN) for r in study_table)
