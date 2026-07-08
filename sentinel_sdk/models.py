"""Typed models for platform API resources.

Plain dataclasses (no pydantic dependency) built from API JSON. Unknown keys
are ignored so old SDK versions keep working when the API adds fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Optional


def _pick(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in names}


@dataclass
class Customer:
    """A customer organization (one WireGuard hub + VPN subnet each)."""

    customer_id: str
    display_name: str = ""
    vpn_subnet: str = ""
    gateway_id: Optional[str] = None
    gateway_endpoint: Optional[str] = None
    gateway_public_key: Optional[str] = None
    hub_alert_url: Optional[str] = None
    hub_provider: Optional[str] = None
    hub_host_id: Optional[str] = None
    status: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Customer":
        return cls(**_pick(cls, data))


@dataclass
class Tower:
    """A Sentry Tower (Jetson) and its lifecycle state."""

    device_id: str
    customer_id: str = ""
    group_id: Optional[str] = None
    vpn_ip: Optional[str] = None
    wg_public_key: Optional[str] = None
    status: str = ""
    acceptance_status: str = ""
    manufactured_at: Optional[str] = None
    enrolled_at: Optional[str] = None
    shipped_at: Optional[str] = None
    rtsp_base: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tower":
        return cls(**_pick(cls, data))

    def rtsp_url(self, camera: int = 1) -> Optional[str]:
        """RTSP URL for a camera (requires WireGuard peer membership to use)."""
        return f"{self.rtsp_base}/cam{camera}" if self.rtsp_base else None


@dataclass
class TowerRegistration:
    """Result of registering a new tower. ``enrollment_token`` is shown ONCE —
    store it securely; the registry keeps only its hash."""

    device_id: str
    customer_id: str
    claim_code: str
    enrollment_token: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TowerRegistration":
        return cls(**_pick(cls, data))


@dataclass
class PTZStatus:
    """Current PTZ position in ONVIF normalized space."""

    pan: float = 0.0
    tilt: float = 0.0
    zoom: float = 0.0

    @classmethod
    def from_result(cls, result: dict[str, Any]) -> "PTZStatus":
        return cls(
            pan=float(result.get("pan", 0.0)),
            tilt=float(result.get("tilt", 0.0)),
            zoom=float(result.get("zoom", 0.0)),
        )


@dataclass
class StreamPath:
    """mediamtx path readiness for one camera."""

    name: str
    ready: bool = False
    readers: int = 0
    source: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StreamPath":
        return cls(**_pick(cls, data))


@dataclass
class Alert:
    """A watchdog alert as delivered by the webhook (see the alerts guide)."""

    device_id: str
    alert_type: str
    severity: str
    timestamp_utc: str
    nonce: str
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Alert":
        return cls(
            device_id=str(data.get("device_id", "")),
            alert_type=str(data.get("alert_type", "")),
            severity=str(data.get("severity", "")),
            timestamp_utc=str(data.get("timestamp_utc", "")),
            nonce=str(data.get("nonce", "")),
            details=dict(data.get("details") or {}),
        )

    @property
    def idempotency_key(self) -> tuple:
        """Alerts are at-least-once — dedupe on this key."""
        return (self.device_id, self.alert_type, self.timestamp_utc, self.nonce)
