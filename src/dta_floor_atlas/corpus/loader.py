"""Load DTA70 datasets via R subprocess.

DTA70 is loaded via R `data(package="DTA70")` from the version-pinned
R-package install. We do NOT vendor or duplicate the data — corpus
reproducibility flows through the upstream R package's version pin.
"""
from __future__ import annotations
from typing import Iterator
from dta_floor_atlas.r_bridge import run_r
from dta_floor_atlas.types import Dataset, StudyRow


_LIST_DATASETS_R = """
suppressPackageStartupMessages(library(DTA70))
suppressPackageStartupMessages(library(jsonlite))
ds <- data(package="DTA70")$results[, "Item"]
cat(toJSON(ds, auto_unbox=FALSE))
"""

_LOAD_DATASET_TEMPLATE = """
suppressPackageStartupMessages(library(DTA70))
suppressPackageStartupMessages(library(jsonlite))
data(NAME, package="DTA70")
df <- get("NAME")
required <- c("TP","FP","FN","TN")
missing <- setdiff(required, names(df))
if (length(missing) > 0) stop(paste("dataset NAME missing columns:", paste(missing, collapse=",")))
prev <- if ("prevalence" %in% names(df)) median(df$prevalence, na.rm=TRUE) else NA
spec <- if ("specialty" %in% names(df)) as.character(df$specialty[1]) else NA
out <- list(
    dataset_id = "NAME",
    n_studies = nrow(df),
    study_table = lapply(seq_len(nrow(df)), function(i) list(
        TP=as.integer(df$TP[i]), FP=as.integer(df$FP[i]),
        FN=as.integer(df$FN[i]), TN=as.integer(df$TN[i])
    )),
    reported_prevalence = if (is.na(prev)) NA_real_ else as.double(prev),
    specialty = if (is.na(spec)) NA_character_ else spec
)
cat(toJSON(out, auto_unbox=TRUE, na="null"))
"""


def _list_dataset_names() -> list[str]:
    out = run_r(_LIST_DATASETS_R)
    return out.parse_json()


def _load_one(name: str) -> Dataset:
    code = _LOAD_DATASET_TEMPLATE.replace("NAME", name)
    out = run_r(code)
    raw = out.parse_json()
    rows = tuple(
        StudyRow(TP=int(r["TP"]), FP=int(r["FP"]), FN=int(r["FN"]), TN=int(r["TN"]))
        for r in raw["study_table"]
    )
    return Dataset(
        dataset_id=raw["dataset_id"],
        n_studies=int(raw["n_studies"]),
        study_table=rows,
        reported_prevalence=raw.get("reported_prevalence"),
        specialty=raw.get("specialty"),
    )


def load_dta70_datasets() -> Iterator[Dataset]:
    """Yield all 76 DTA70 datasets in declaration order."""
    for name in _list_dataset_names():
        yield _load_one(name)
