"""HMAC verification for Kallon alert webhooks.

Towers sign every alert POST with HMAC-SHA256 over the raw request body using
the shared ``alert.key`` and send it as ``X-Kallon-Signature: sha256=<hex>``.
The canonical body is compact JSON with sorted keys — always verify against
the **raw bytes you received**, never a re-serialized copy.

Usage (any web framework)::

    from sentinel_sdk.alerts import AlertVerifier

    verifier = AlertVerifier.from_key_file("/etc/kallon/alert.key")

    # in your webhook handler:
    if not verifier.verify(raw_body_bytes, request.headers.get("X-Kallon-Signature", "")):
        return 401
    alert = verifier.parse(raw_body_bytes)
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Union

from .models import Alert

SIGNATURE_HEADER = "X-Kallon-Signature"


def sign_alert(body: bytes, key: bytes) -> str:
    """Compute the signature header value for a raw body (``sha256=<hex>``).

    This is what the tower watchdog produces; exposed for tests and tooling.
    """
    return "sha256=" + hmac.new(key, body, hashlib.sha256).hexdigest()


def verify_alert(body: bytes, signature_header: str, key: bytes) -> bool:
    """Constant-time verification of ``X-Kallon-Signature`` against a raw body."""
    expected = hmac.new(key, body, hashlib.sha256).hexdigest()
    provided = signature_header.strip()
    if provided.startswith("sha256="):
        provided = provided[len("sha256="):]
    return hmac.compare_digest(expected, provided)


def canonical_body(alert: dict) -> bytes:
    """Serialize an alert dict exactly as the tower does (compact, sorted keys).

    Only needed when *producing* signed alerts (e.g. test fixtures) — for
    verification always use the raw received bytes.
    """
    return json.dumps(alert, sort_keys=True, separators=(",", ":")).encode("utf-8")


class AlertVerifier:
    """Bound-key convenience wrapper around :func:`verify_alert`."""

    def __init__(self, key: Union[bytes, str]) -> None:
        self._key = key.encode("utf-8") if isinstance(key, str) else key

    @classmethod
    def from_key_file(cls, path: Union[str, Path]) -> "AlertVerifier":
        """Load the shared secret from an ``alert.key`` file (whitespace-stripped)."""
        return cls(Path(path).read_bytes().strip())

    def verify(self, body: bytes, signature_header: str) -> bool:
        return verify_alert(body, signature_header, self._key)

    def sign(self, body: bytes) -> str:
        return sign_alert(body, self._key)

    @staticmethod
    def parse(body: bytes) -> Alert:
        """Parse a verified body into an :class:`~sentinel_sdk.models.Alert`."""
        return Alert.from_dict(json.loads(body.decode("utf-8")))
