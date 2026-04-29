"""Shared helpers for R-backed engines: continuity-correction logic + study-table
JSON serialization for env-var injection.

Windows limit: os.environ values are capped at 32,767 chars. For large datasets
(k~1000), the JSON study table exceeds this limit. Use set_study_table_env() to
transparently handle large payloads by writing to a temp file and setting
DTA_STUDY_TABLE_FILE instead of DTA_STUDY_TABLE_JSON.
"""
from __future__ import annotations
import json, os, tempfile
from contextlib import contextmanager
from dta_floor_atlas.types import Dataset, StudyRow

# Windows hard limit on environment variable value length.
_WIN_ENV_MAX = 32000  # slightly under 32767 to be safe


def study_table_to_r_json(study_table: tuple[StudyRow, ...]) -> str:
    """Serialize study table to JSON consumable by R fromJSON()."""
    return json.dumps([
        {"TP": r.TP, "FP": r.FP, "FN": r.FN, "TN": r.TN}
        for r in study_table
    ])


@contextmanager
def study_table_env(study_table: tuple[StudyRow, ...], add_cc: bool):
    """Context manager: set DTA_STUDY_TABLE_JSON (or DTA_STUDY_TABLE_FILE for large
    datasets) and DTA_ADD_CONTINUITY in os.environ, restoring on exit.

    For datasets where the JSON exceeds _WIN_ENV_MAX, writes the JSON to a temp
    file and sets DTA_STUDY_TABLE_FILE to the path. The R scripts check both vars:
    they read DTA_STUDY_TABLE_FILE first (if set), else fall back to DTA_STUDY_TABLE_JSON.
    """
    sj = study_table_to_r_json(study_table)
    use_file = len(sj) >= _WIN_ENV_MAX

    env_vars = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_STUDY_TABLE_FILE": os.environ.get("DTA_STUDY_TABLE_FILE"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }

    tmp_path: str | None = None
    try:
        if use_file:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(sj)
                tmp_path = tmp.name
            os.environ["DTA_STUDY_TABLE_FILE"] = tmp_path
            os.environ.pop("DTA_STUDY_TABLE_JSON", None)
        else:
            os.environ["DTA_STUDY_TABLE_JSON"] = sj
            os.environ.pop("DTA_STUDY_TABLE_FILE", None)
        os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
        yield sj  # caller can use the JSON string if needed
    finally:
        for k, v in env_vars.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if tmp_path and os.path.isfile(tmp_path):
            os.unlink(tmp_path)


def needs_continuity(study_table: tuple[StudyRow, ...]) -> bool:
    """True if any study has a zero cell (per advanced-stats.md: only then add 0.5)."""
    return any(0 in (r.TP, r.FP, r.FN, r.TN) for r in study_table)
