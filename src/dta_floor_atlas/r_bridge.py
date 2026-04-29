"""R subprocess wrapper. Single boundary for all R interop in the engines."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, threading
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


def _run_subprocess_with_timeout(cmd: list[str], timeout_s: int, env: dict) -> tuple[str, str, int]:
    """Run a subprocess with a hard timeout that reliably kills on Windows.

    On Windows, subprocess.run(timeout=N) raises TimeoutExpired then calls
    process.kill() followed by process.communicate() to drain pipes.  If the
    killed process does not release its pipe handles quickly (common with R's
    native DLL code), the communicate() call can block indefinitely even after
    the kill — causing the Python caller to hang.

    Fix: use Popen + a daemon thread that calls communicate().  The main thread
    waits for the thread to finish within timeout_s seconds.  If it doesn't, we
    force-kill the process and close the pipes explicitly, then wait briefly for
    the thread to drain (with a hard 5-second cap) before giving up.

    Returns (stdout, stderr, returncode).  Raises RTimeout if the timeout fires.
    """
    # CREATE_NO_WINDOW suppresses a flashing console on Windows.
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        **kwargs,
    )

    result: list = [None, None, None]  # [stdout, stderr, returncode]

    def _communicate():
        try:
            out, err = proc.communicate()
            result[0] = out
            result[1] = err
            result[2] = proc.returncode
        except Exception:
            result[0] = result[0] or ""
            result[1] = result[1] or ""
            result[2] = result[2] if result[2] is not None else -1

    t = threading.Thread(target=_communicate, daemon=True)
    t.start()
    t.join(timeout=timeout_s)

    if t.is_alive():
        # Timeout: kill the process, then close pipes to unblock communicate().
        try:
            proc.kill()
        except OSError:
            pass
        # Close the pipe ends on the Python side so communicate() can drain.
        for f in (proc.stdout, proc.stderr):
            try:
                if f:
                    f.close()
            except OSError:
                pass
        # Give the thread 5 more seconds to exit after pipe close.
        t.join(timeout=5)
        raise RTimeout(f"R call exceeded {timeout_s}s")

    return result[0] or "", result[1] or "", result[2] if result[2] is not None else -1


def run_r(
    code: str,
    timeout_s: int = 300,
    raise_on_error: bool = True,
) -> RCallResult:
    """Execute R code via Rscript subprocess.

    Args:
        code: R expression(s) to evaluate. Use cat() to emit stdout.
        timeout_s: per-call timeout in seconds.  Default 300s — large DTA
            datasets (k>100) can take 2-3 minutes for bivariate REML.
            Windows note: uses a thread-based kill to avoid pipe-deadlock
            after TerminateProcess() (see _run_subprocess_with_timeout).
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
    # On Windows, passing multiline code via Rscript -e causes a crash
    # (exit 0xC0000005 / access violation) when the shell splits on newlines.
    # Use a temp file for any code containing newlines; keep -e for single-line
    # calls so that all existing single-expression callers are unaffected.
    tmp_path: str | None = None
    try:
        if "\n" in code.strip():
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".R", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            cmd = [rscript, tmp_path]
        else:
            cmd = [rscript, "-e", code]
        # Pass current environment so env vars (DTA_STUDY_TABLE_JSON, etc.) are inherited.
        try:
            stdout, stderr, returncode = _run_subprocess_with_timeout(
                cmd, timeout_s, env=os.environ.copy()
            )
        except RTimeout:
            raise
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            os.unlink(tmp_path)

    result = RCallResult(
        stdout=stdout,
        stderr=stderr,
        exit_status=returncode,
        r_version=_r_version(rscript),
        call_string=code,
    )
    if raise_on_error and result.exit_status != 0:
        raise RError(f"R exited {result.exit_status}: {result.stderr[:200]}")
    return result
