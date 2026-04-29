"""Test the R subprocess wrapper."""
import pytest
from dta_floor_atlas.r_bridge import run_r, RCallResult, RTimeout, RError


def test_run_r_returns_simple_value():
    result = run_r("cat(1 + 1)")
    assert isinstance(result, RCallResult)
    assert result.exit_status == 0
    assert "2" in result.stdout


def test_run_r_returns_json_parsed():
    result = run_r('cat(jsonlite::toJSON(list(x=1.5, y="hello"), auto_unbox=TRUE))')
    assert result.exit_status == 0
    parsed = result.parse_json()
    assert parsed == {"x": 1.5, "y": "hello"}


def test_run_r_records_versions():
    result = run_r("cat(1)")
    assert result.r_version is not None
    assert "4." in result.r_version


def test_run_r_raises_on_timeout():
    with pytest.raises(RTimeout):
        run_r("Sys.sleep(10); cat(1)", timeout_s=1)


def test_run_r_returns_error_on_nonzero_exit():
    result = run_r("stop('intentional')", raise_on_error=False)
    assert result.exit_status != 0
    assert "intentional" in result.stderr


def test_run_r_raises_on_error_by_default():
    with pytest.raises(RError):
        run_r("stop('intentional')")
