"""Unit tests for HMAC alert verification (mirrors the tower's signing)."""
from __future__ import annotations

import hashlib
import hmac

from sentinel_sdk.alerts import AlertVerifier, canonical_body, sign_alert, verify_alert

KEY = b"test-alert-key-32-bytes-aaaaaaaa"

ALERT = {
    "device_id": "kln_acme_000042",
    "timestamp_utc": "2026-07-08T14:30:00Z",
    "nonce": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "alert_type": "tamper_impact",
    "severity": "critical",
    "details": {"axis_mg": 312, "threshold_mg": 150},
}


def test_sign_matches_tower_algorithm():
    body = canonical_body(ALERT)
    expected = "sha256=" + hmac.new(KEY, body, hashlib.sha256).hexdigest()
    assert sign_alert(body, KEY) == expected


def test_verify_roundtrip():
    body = canonical_body(ALERT)
    sig = sign_alert(body, KEY)
    assert verify_alert(body, sig, KEY) is True


def test_verify_without_prefix():
    body = canonical_body(ALERT)
    sig = sign_alert(body, KEY).removeprefix("sha256=")
    assert verify_alert(body, sig, KEY) is True


def test_verify_rejects_tampered_body():
    body = canonical_body(ALERT)
    sig = sign_alert(body, KEY)
    tampered = body.replace(b"critical", b"info")
    assert verify_alert(tampered, sig, KEY) is False


def test_verify_rejects_wrong_key():
    body = canonical_body(ALERT)
    sig = sign_alert(body, KEY)
    assert verify_alert(body, sig, b"other-key") is False


def test_verifier_class_and_parse(tmp_path):
    key_file = tmp_path / "alert.key"
    key_file.write_bytes(KEY + b"\n")  # trailing newline must be stripped
    verifier = AlertVerifier.from_key_file(key_file)

    body = canonical_body(ALERT)
    assert verifier.verify(body, verifier.sign(body)) is True

    alert = verifier.parse(body)
    assert alert.device_id == "kln_acme_000042"
    assert alert.alert_type == "tamper_impact"
    assert alert.details["axis_mg"] == 312
    assert alert.idempotency_key == (
        "kln_acme_000042", "tamper_impact", "2026-07-08T14:30:00Z",
        "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    )
