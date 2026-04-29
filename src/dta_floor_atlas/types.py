"""Shared dataclass types — Dataset, StudyRow, FitResult."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class StudyRow:
    """One study's 2x2 contingency table from a DTA review."""
    TP: int
    FP: int
    FN: int
    TN: int

    @property
    def n_diseased(self) -> int:
        return self.TP + self.FN

    @property
    def n_healthy(self) -> int:
        return self.FP + self.TN

    @property
    def n_total(self) -> int:
        return self.n_diseased + self.n_healthy


@dataclass(frozen=True)
class Dataset:
    """One DTA review's complete data."""
    dataset_id: str
    n_studies: int
    study_table: tuple[StudyRow, ...]
    reported_prevalence: float | None = None
    specialty: str | None = None


CascadeLevel = Literal[1, 2, 3, "inf", "n/a"]
EngineName = Literal["canonical", "copula", "reitsma", "moses", "archaic", "ems", "gds"]


@dataclass(frozen=True)
class FitResult:
    """Per-engine, per-dataset fit outcome.

    Schema matches spec section 9.1 — EVERY field present even on failure
    (use None for unavailable values, never silent defaults).
    """
    dataset_id: str
    engine: EngineName
    cascade_level: CascadeLevel
    converged: bool
    pooled_se: float | None
    pooled_sp: float | None
    pooled_se_ci: tuple[float, float] | None
    pooled_sp_ci: tuple[float, float] | None
    rho: float | None
    tau2_logit_se: float | None
    tau2_logit_sp: float | None
    auc_partial: float | None
    r_version: str | None
    package_version: str | None
    call_string: str | None
    exit_status: int
    convergence_reason: str | None
    raw_stdout_sha256: str | None
