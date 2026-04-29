# tests/test_signing.py
"""Test HMAC-SHA256 signing of result bundles. Key from env, never embedded."""
import json, os
import pytest
from dta_floor_atlas.signing import sign_bundle, verify_bundle, SigningKeyMissing


def test_sign_requires_env_key(tmp_path, monkeypatch):
    monkeypatch.delenv("TRUTHCERT_HMAC_KEY", raising=False)
    with pytest.raises(SigningKeyMissing):
        sign_bundle({"data": 1})


def test_sign_with_env_key_produces_signature(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key_do_not_use_in_prod")
    signed = sign_bundle({"data": 1})
    assert "signature" in signed
    assert "data" in signed["payload"]


def test_verify_round_trip(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    bundle = sign_bundle({"floor_1_pct": 22.5})
    assert verify_bundle(bundle) is True


def test_verify_rejects_tampered_payload(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    bundle = sign_bundle({"floor_1_pct": 22.5})
    bundle["payload"]["floor_1_pct"] = 99.9  # tamper
    assert verify_bundle(bundle) is False


def test_verify_constant_time_compare_used():
    """Signing should use hmac.compare_digest, not == — but the API is verify=bool, so
    we just confirm the implementation imports hmac.compare_digest."""
    import dta_floor_atlas.signing as mod
    src = open(mod.__file__).read()
    assert "hmac.compare_digest" in src, "Must use constant-time comparison per TruthCert lesson"
