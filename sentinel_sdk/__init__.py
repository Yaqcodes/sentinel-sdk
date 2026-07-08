"""Sentinel SDK — official Python client for the Kallon Sentry Tower platform.

Quick start::

    from sentinel_sdk import SentinelClient

    client = SentinelClient("https://api.terra.example")
    for tower in client.list_towers():
        print(tower.device_id, tower.status, tower.rtsp_base)

Webhook verification::

    from sentinel_sdk import AlertVerifier

    verifier = AlertVerifier.from_key_file("/etc/kallon/alert.key")
    ok = verifier.verify(raw_body, request.headers["X-Kallon-Signature"])
"""
from .alerts import AlertVerifier, sign_alert, verify_alert
from .client import SentinelClient
from .exceptions import (
    APIError,
    AuthError,
    InvalidRequestError,
    NotFoundError,
    SentinelError,
    TowerError,
    TowerNotEnrolledError,
    TowerOfflineError,
    TransportError,
)
from .models import Alert, Customer, PTZStatus, StreamPath, Tower, TowerRegistration

__version__ = "0.1.0"

__all__ = [
    "SentinelClient",
    "AlertVerifier",
    "verify_alert",
    "sign_alert",
    "Alert",
    "Customer",
    "Tower",
    "TowerRegistration",
    "PTZStatus",
    "StreamPath",
    "SentinelError",
    "TransportError",
    "APIError",
    "AuthError",
    "NotFoundError",
    "InvalidRequestError",
    "TowerNotEnrolledError",
    "TowerOfflineError",
    "TowerError",
]
