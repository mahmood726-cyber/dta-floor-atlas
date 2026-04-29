"""Emit corpus_manifest.jsonl — one line per dataset with sha256 of its study table."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from dta_floor_atlas.corpus.loader import load_dta70_datasets


def _study_table_sha256(study_table) -> str:
    canonical = json.dumps(
        [(r.TP, r.FP, r.FN, r.TN) for r in study_table],
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_corpus_manifest(out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for d in load_dta70_datasets():
            rec = {
                "dataset_id": d.dataset_id,
                "n_studies": d.n_studies,
                "reported_prevalence": d.reported_prevalence,
                "specialty": d.specialty,
                "study_table_sha256": _study_table_sha256(d.study_table),
            }
            f.write(json.dumps(rec, sort_keys=True) + "\n")
            n += 1
    return n
