"""R subprocess wrapper. Single boundary for all R interop in the engines."""
from __future__ import annotations
import json, os, shutil, subprocess
from dataclasses import dataclass


class RTimeout(Exception):
    pass


class RError(Exception):
    pass


# Fallback locations for Rscript when not on PATH (Windows convention).
# Mirrors scripts/preflight_prereqs.py — single source of truth would be ideal
# but we keep these tightly scoped here to avoid coupling to a shared helper.
_RSCRIPT_FALLBACKS = (
    r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe",
    r"C:\Program Files\R\R-4.5.3\bin\Rscript.exe",
)


def _find_rscript() -> str:
    """Locate Rscript via PATH or known Windows install dirs.

    Raises RError if not found anywhere — engines need R; failing fast
    is better than a confusing FileNotFoundError later.
    """
    p = shutil.which("Rscript")
    if p:
        return p
    for cand in _RSCRIPT_FALLBACKS:
        if os.path.isfile(cand):
            return cand
    raise RError(
        "Rscript not found on PATH or at known Windows fallback locations. "
        "Install R 4.5.x and ensure Rscript.exe is reachable, or extend "
        "_RSCRIPT_FALLBACKS in r_bridge.py."
    )


@dataclass(frozen=True)
class RCallResult:
    stdout: str
    stderr: str
    exit_status: int
    r_version: str | None
    call_string: str

    def parse_json(self) -> dict | list:
        return json.loads(self.stdout)


def _r_version(rscript: str) -> str:
    out = subprocess.run([rscript, "--version"], capture_output=True, text=True, timeout=10)
    text = (out.stderr or "") + (out.stdout or "")
    for line in text.splitlines():
        if "version" in line.lower():
            return line.strip()
    return text.strip().splitlines()[0] if text.strip() else "unknown"


def run_r(
    code: str,
    timeout_s: int = 60,
    raise_on_error: bool = True,
) -> RCallResult:
    """Execute R code via Rscript subprocess.

    Args:
        code: R expression(s) to evaluate. Use cat() to emit stdout.
        timeout_s: per-call timeout. Default 60s matches spec error-handling §11.2.
        raise_on_error: if True, raise RError on non-zero exit. If False, return
            the RCallResult with the failure recorded — for floor analysis
            where R failure is data, not exception.

    Returns:
        RCallResult with stdout, stderr, exit code, R version, and call string.

    Raises:
        RTimeout if timeout_s exceeded.
        RError if raise_on_error and exit_status != 0, OR if Rscript itself
            cannot be located on PATH or fallback locations.
    """
    rscript = _find_rscript()
    try:
        out = subprocess.run(
            [rscript, "-e", code],
            capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        raise RTimeout(f"R call exceeded {timeout_s}s: {code[:80]}") from e

    result = RCallResult(
        stdout=out.stdout,
        stderr=out.stderr,
        exit_status=out.returncode,
        r_version=_r_version(rscript),
        call_string=code,
    )
    if raise_on_error and result.exit_status != 0:
        raise RError(f"R exited {result.exit_status}: {result.stderr[:200]}")
    return result
