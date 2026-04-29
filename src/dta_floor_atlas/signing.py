"""HMAC-SHA256 signing for result bundles.

Key sourcing: env var TRUTHCERT_HMAC_KEY only. Never embedded.
Per TruthCert lesson 2026-04-14: any forgeable signature is a P0 security bug.

Constant-time comparison via hmac.compare_digest on verify path.
"""
from __future__ import annotations
import hashlib, hmac, json, os


class SigningKeyMissing(Exception):
    """Raised when TRUTHCERT_HMAC_KEY env var is unset."""


def _get_key() -> bytes:
    key = os.environ.get("TRUTHCERT_HMAC_KEY")
    if not key:
        raise SigningKeyMissing(
            "TRUTHCERT_HMAC_KEY env var is required. "
            "Set it from ~/.config/dta-floor-hmac.key or pass via shell. "
            "Never embed the key in source."
        )
    return key.encode("utf-8")


def _str_keys(obj):
    """Recursively convert dict keys to strings for canonical JSON serialisation.

    json.dumps(sort_keys=True) raises TypeError when a dict contains mixed
    int/str keys (e.g. by_level = {1: 59, 'inf': 2}).  Converting all keys to
    str first gives a stable, comparable canonical form.
    """
    if isinstance(obj, dict):
        return {str(k): _str_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_str_keys(v) for v in obj]
    return obj


def _canonical_payload(payload: dict) -> bytes:
    return json.dumps(_str_keys(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_bundle(payload: dict) -> dict:
    """Wrap payload in a signed bundle: {payload, signature, sig_algo}."""
    key = _get_key()
    canonical = _canonical_payload(payload)
    sig = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    return {
        "payload": payload,
        "signature": sig,
        "sig_algo": "HMAC-SHA256",
    }


def verify_bundle(bundle: dict) -> bool:
    """Constant-time verify of bundle signature against env key."""
    if "payload" not in bundle or "signature" not in bundle:
        return False
    try:
        key = _get_key()
    except SigningKeyMissing:
        return False
    expected = hmac.new(key, _canonical_payload(bundle["payload"]), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, bundle["signature"])
