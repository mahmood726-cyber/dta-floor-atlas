import json
from pathlib import Path
from dta_floor_atlas.corpus.manifest import write_corpus_manifest


def test_manifest_writes_one_line_per_dataset(tmp_path):
    out = tmp_path / "corpus_manifest.jsonl"
    n = write_corpus_manifest(out)
    assert n == 76
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 76


def test_manifest_each_line_has_required_keys(tmp_path):
    out = tmp_path / "corpus_manifest.jsonl"
    write_corpus_manifest(out)
    for line in out.read_text().strip().splitlines():
        rec = json.loads(line)
        assert {"dataset_id", "n_studies", "study_table_sha256"} <= set(rec.keys())


def test_manifest_sha256_is_deterministic(tmp_path):
    """Two runs produce identical bytes (idempotency invariant)."""
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    write_corpus_manifest(a)
    write_corpus_manifest(b)
    assert a.read_bytes() == b.read_bytes(), "Manifest must be bytewise idempotent"
