"""Exception hierarchy for the Sentinel SDK.

Every error raised by :class:`sentinel_sdk.SentinelClient` derives from
:class:`SentinelError`, so ``except SentinelError`` catches everything the SDK
can raise. Specific subclasses map to the platform error contract
(``{"error": {"code": ..., "message": ...}}`` — see the platform API docs).
"""
from __future__ import annotations

from typing import Any, Optional


class SentinelError(Exception):
    """Base class for all SDK errors."""


class TransportError(SentinelError):
    """The control plane itself could not be reached (network/DNS/TLS)."""


class APIError(SentinelError):
    """The API returned an error response.

    Attributes:
        status_code: HTTP status code.
        code: machine error code from the error envelope (e.g. ``not_found``).
        message: human-readable message.
        context: any extra fields the envelope carried (e.g. ``device_id``).
    """

    def __init__(self, status_code: int, code: str, message: str,
                 context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(f"[{status_code} {code}] {message}")
        self.status_code = status_code
        self.code = code
        self.message = message
        self.context = context or {}


class AuthError(APIError):
    """401 — missing or invalid API key."""


class NotFoundError(APIError):
    """404 — unknown customer, tower, or camera."""


class InvalidRequestError(APIError):
    """422 — malformed request body or parameters."""


class TowerNotEnrolledError(APIError):
    """409 ``tower_not_enrolled`` — the tower is registered but has not
    completed first-boot enrollment, so it has no VPN address yet."""


class TowerOfflineError(APIError):
    """503 ``tower_offline`` — the tower did not respond over the VPN
    (tunnel down, tower rebooting, or power loss)."""

    @property
    def device_id(self) -> Optional[str]:
        return self.context.get("device_id")


class TowerError(APIError):
    """502 ``tower_error`` — the tower was reached but its gateway reported a
    failure (e.g. PTZ daemon down, ffmpeg failure)."""
