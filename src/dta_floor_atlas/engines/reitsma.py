"""Reitsma SROC via R mada::reitsma.

Reference: Reitsma 2005 (the original bivariate paper); mada implementation
by Doebler 2015. Default specification — no custom priors or constraints.

mada 1.x summary() coefficient matrix row names verified 2026-04-28:
  rownames: tsens.(Intercept), tfpr.(Intercept), sensitivity, false pos. rate
  colnames: Estimate, Std. Error, z, Pr(>|z|), 95%ci.lb, 95%ci.ub
AUC(fit) returns a list: $AUC (full SROC AUC) and $pAUC (partial).
We store $AUC as auc_partial per the FitResult field convention.
"""
from __future__ import annotations
import hashlib
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_env, needs_continuity


_FIT_REITSMA_R = r"""
suppressPackageStartupMessages({library(mada); library(jsonlite)})
dta_file <- Sys.getenv("DTA_STUDY_TABLE_FILE")
if (nchar(dta_file) > 0) {
  df <- fromJSON(readLines(dta_file, warn=FALSE))
} else {
  df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
}
add_cc <- as.logical(Sys.getenv("DTA_ADD_CONTINUITY"))
if (add_cc) {
  df$TP <- df$TP + 0.5; df$FP <- df$FP + 0.5
  df$FN <- df$FN + 0.5; df$TN <- df$TN + 0.5
}

ok <- TRUE
fit <- tryCatch(reitsma(df), error = function(e) { ok <<- FALSE; e })
if (!ok) {
  cat(toJSON(list(converged=FALSE, reason=as.character(fit$message)), auto_unbox=TRUE))
  quit(save="no")
}

s <- summary(fit)
# mada reports pooled estimates in the "Estimate" column.
# Verified rownames: "sensitivity" and "false pos. rate"
pooled_se  <- as.numeric(s$coefficients["sensitivity",    "Estimate"])
pooled_fpr <- as.numeric(s$coefficients["false pos. rate","Estimate"])
pooled_sp  <- 1 - pooled_fpr
# AUC(fit) returns a list; $AUC holds the full SROC area under curve
auc <- tryCatch(as.numeric(AUC(fit)$AUC), error = function(e) NA)

cat(toJSON(list(
  converged    = TRUE,
  pooled_se    = pooled_se,
  pooled_sp    = pooled_sp,
  auc_partial  = auc,
  mada_version = as.character(packageVersion("mada"))
), auto_unbox=TRUE, na="null", digits=15))
"""


def fit_reitsma(d: Dataset, *, raise_on_error: bool = False) -> FitResult:
    add_cc = needs_continuity(d.study_table)
    with study_table_env(d.study_table, add_cc):
        try:
            res = run_r(_FIT_REITSMA_R, raise_on_error=raise_on_error)
        except (RTimeout, RError) as e:
            return _failed(d, reason=type(e).__name__, exit_status=1)
        if res.exit_status != 0:
            return _failed(d, reason="r_error", exit_status=res.exit_status,
                           raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        try:
            parsed = res.parse_json()
        except Exception:
            return _failed(d, reason="malformed_output", exit_status=res.exit_status,
                           raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        if not parsed.get("converged"):
            return _failed(d, reason=parsed.get("reason", "non_convergence"),
                           exit_status=res.exit_status, r_version=res.r_version)
        return FitResult(
            dataset_id=d.dataset_id, engine="reitsma", cascade_level="n/a",
            converged=True, pooled_se=parsed["pooled_se"], pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None, pooled_sp_ci=None,
            rho=None, tau2_logit_se=None, tau2_logit_sp=None,
            auc_partial=parsed.get("auc_partial"),
            r_version=res.r_version, package_version=parsed.get("mada_version"),
            call_string="mada::reitsma(df)",
            exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
        )


def _failed(d, *, reason, exit_status, r_version=None, raw_stdout_sha256=None) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine="reitsma", cascade_level="n/a", converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=r_version, package_version=None,
        call_string="mada::reitsma(...)", exit_status=exit_status,
        convergence_reason=reason, raw_stdout_sha256=raw_stdout_sha256,
    )
