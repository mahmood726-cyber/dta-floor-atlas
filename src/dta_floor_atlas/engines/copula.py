"""CopulaREMADA via R CopulaREMADA::CopulaREMADA.norm.

Clayton 270 degree rotated copula with normal margins, Gauss-Legendre
quadrature with nq=15 nodes. This is the package's own default example.

Substituted for HSROC at v0.1: HSROC was archived from CRAN in 2024 with
no R 4.5 source build. CopulaREMADA provides a paradigmatically-different
SROC alternative via copula random effects.

Reference: Nikoloulopoulos AK (2015). Stat Methods Med Res 24(6):780-805.
"""
from __future__ import annotations
import hashlib, os
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


_FIT_COPULA_R = r"""
suppressPackageStartupMessages({
  library(CopulaREMADA); library(statmod); library(matlab); library(jsonlite)
})
df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
add_cc <- as.logical(Sys.getenv("DTA_ADD_CONTINUITY"))
if (add_cc) {
  df$TP <- df$TP + 0.5; df$FP <- df$FP + 0.5
  df$FN <- df$FN + 0.5; df$TN <- df$TN + 0.5
}

nq <- 15
gl <- gauss.quad.prob(nq, "uniform")
# gauss.quad.prob returns $nodes and $weights (not $n/$w)
mgrid <- meshgrid(gl$nodes, gl$nodes)

ok <- TRUE
fit <- tryCatch(
  CopulaREMADA.norm(TP=df$TP, FN=df$FN, FP=df$FP, TN=df$TN,
                    gl=gl, mgrid=mgrid,
                    qcond=qcondcln270, tau2par=tau2par.cln270),
  error = function(e) { ok <<- FALSE; e }
)
if (!ok) {
  cat(toJSON(list(converged=FALSE, reason=as.character(fit$message)), auto_unbox=TRUE))
  quit(save="no")
}

# CopulaREMADA.norm wraps nlm(). fit$estimate holds the MLE parameter vector:
#   [1] = pooled Se (probability scale, initialised as mean(Se_i))
#   [2] = pooled Sp (probability scale, initialised as mean(Sp_i))
#   [3] = sigma_Se (logit scale heterogeneity)
#   [4] = sigma_Sp (logit scale heterogeneity)
#   [5] = Kendall tau (copula dependence)
# nlm code 1-3 indicate acceptable convergence; 4-5 indicate failure.
nlm_code <- as.integer(fit$code)
if (nlm_code >= 4) {
  cat(toJSON(list(converged=FALSE, reason=paste("nlm_code", nlm_code)), auto_unbox=TRUE))
  quit(save="no")
}

pooled_se <- as.numeric(fit$estimate[1])
pooled_sp <- as.numeric(fit$estimate[2])

cat(toJSON(list(
  converged = TRUE,
  pooled_se = pooled_se,
  pooled_sp = pooled_sp,
  nlm_code = nlm_code,
  copula_version = as.character(packageVersion("CopulaREMADA"))
), auto_unbox=TRUE, na="null", digits=15))
"""


def fit_copula(d: Dataset, *, raise_on_error: bool = False) -> FitResult:
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(_FIT_COPULA_R, timeout_s=300, raise_on_error=raise_on_error)
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
            dataset_id=d.dataset_id, engine="copula", cascade_level="n/a",
            converged=True,
            pooled_se=parsed["pooled_se"], pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None, pooled_sp_ci=None,
            rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
            r_version=res.r_version, package_version=parsed.get("copula_version"),
            call_string="CopulaREMADA::CopulaREMADA.norm(qcond=qcondcln270, tau2par=tau2par.cln270, nq=15)",
            exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def _failed(d, *, reason, exit_status, r_version=None, raw_stdout_sha256=None) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine="copula", cascade_level="n/a", converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=r_version, package_version=None,
        call_string="CopulaREMADA::CopulaREMADA.norm(...)", exit_status=exit_status,
        convergence_reason=reason, raw_stdout_sha256=raw_stdout_sha256,
    )
