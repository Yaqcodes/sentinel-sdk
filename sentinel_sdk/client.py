"""SentinelClient — typed Python client for the Kallon platform API.

One client, one base URL (the Terra control plane). Tower-specific calls
(PTZ, snapshots, sensors) are proxied by the control plane over the VPN —
the SDK never talks to a tower directly.

Example::

    from sentinel_sdk import SentinelClient

    client = SentinelClient("https://api.terra.example")   # api_key="..." when auth lands
    towers = client.list_towers()
    client.ptz_move("kln_acme_000042", camera=1, pan=0.5, tilt=-0.2)
    jpeg = client.snapshot("kln_acme_000042", camera=1)
    open("frame.jpg", "wb").write(jpeg)
"""
from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from .exceptions import (
    APIError,
    AuthError,
    InvalidRequestError,
    NotFoundError,
    TowerError,
    TowerNotEnrolledError,
    TowerOfflineError,
    TransportError,
)
from .models import Customer, PTZStatus, StreamPath, Tower, TowerRegistration

_ERROR_CLASSES: dict[str, type[APIError]] = {
    "unauthorized": AuthError,
    "not_found": NotFoundError,
    "invalid_request": InvalidRequestError,
    "tower_not_enrolled": TowerNotEnrolledError,
    "tower_offline": TowerOfflineError,
    "tower_error": TowerError,
}


class SentinelClient:
    """Synchronous client for the Kallon platform API.

    Args:
        base_url: control plane base URL, e.g. ``https://api.terra.example``.
        api_key: optional API key sent as ``X-Kallon-Api-Key``. Not enforced
            by the platform yet, but set it now so your code is ready when
            enforcement lands.
        timeout: default per-request timeout in seconds. Snapshot and PTZ
            calls use a longer budget automatically (VPN + camera latency).
        transport: optional httpx transport (used by tests for mocking).
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: Optional[str] = None,
        timeout: float = 15.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        headers = {"Accept": "application/json"}
        if api_key:
            headers["X-Kallon-Api-Key"] = api_key
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    # ── lifecycle ────────────────────────────────────────────────────────────
    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SentinelClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ── plumbing ─────────────────────────────────────────────────────────────
    def _request(self, method: str, path: str, *, timeout: Optional[float] = None,
                 **kwargs: Any) -> httpx.Response:
        try:
            resp = self._http.request(
                method, path, timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise TransportError(f"could not reach control plane: {exc}") from exc
        if resp.status_code < 400:
            return resp
        raise self._to_error(resp)

    @staticmethod
    def _to_error(resp: httpx.Response) -> APIError:
        code, message, context = "unknown_error", resp.text[:300], {}
        try:
            body = resp.json()
        except json.JSONDecodeError:
            body = None
        if isinstance(body, dict):
            if isinstance(body.get("error"), dict):
                err = body["error"]
                code = str(err.get("code", code))
                message = str(err.get("message", message))
                context = {k: v for k, v in err.items() if k not in ("code", "message")}
            elif "detail" in body:  # enrollment endpoints keep FastAPI shape
                code = {401: "unauthorized", 404: "not_found", 409: "conflict",
                        422: "invalid_request"}.get(resp.status_code, "api_error")
                message = str(body["detail"])
        cls = _ERROR_CLASSES.get(code, APIError)
        return cls(resp.status_code, code, message, context)

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._request(method, path, **kwargs).json()

    # ── fleet ────────────────────────────────────────────────────────────────
    def list_customers(self) -> list[Customer]:
        data = self._json("GET", "/v1/customers")
        return [Customer.from_dict(c) for c in data.get("customers", [])]

    def get_customer(self, customer_id: str) -> Customer:
        return Customer.from_dict(self._json("GET", f"/v1/customers/{customer_id}"))

    def list_customer_towers(self, customer_id: str) -> list[Tower]:
        data = self._json("GET", f"/v1/customers/{customer_id}/towers")
        return [Tower.from_dict(t) for t in data.get("towers", [])]

    def list_towers(self, status: Optional[str] = None) -> list[Tower]:
        params = {"status": status} if status else None
        data = self._json("GET", "/v1/towers", params=params)
        return [Tower.from_dict(t) for t in data.get("towers", [])]

    def get_tower(self, device_id: str) -> Tower:
        return Tower.from_dict(self._json("GET", f"/v1/towers/{device_id}"))

    def register_tower(self, customer_id: str, serial: int,
                       group_id: Optional[str] = None) -> TowerRegistration:
        """Register a new tower (factory flow). Returns a ONE-TIME enrollment
        token — store it securely, it cannot be retrieved again."""
        body = {"customer_id": customer_id, "serial": serial, "group_id": group_id}
        return TowerRegistration.from_dict(self._json("POST", "/v1/towers", json=body))

    # ── tower: PTZ ───────────────────────────────────────────────────────────
    def ptz_move(self, device_id: str, *, camera: int = 1, pan: float, tilt: float,
                 zoom: Optional[float] = None, timeout: float = 30.0) -> dict[str, Any]:
        """Absolute PTZ move. pan/tilt in [-1, 1], zoom in [0, 1] (ONVIF
        normalized space). Blocks until the camera confirms (~1-2 s typical)."""
        body: dict[str, Any] = {"camera": camera, "mode": "absolute", "pan": pan, "tilt": tilt}
        if zoom is not None:
            body["zoom"] = zoom
        return self._json("POST", f"/v1/towers/{device_id}/ptz/move", json=body, timeout=timeout)

    def ptz_move_continuous(self, device_id: str, *, camera: int = 1, pan: float,
                            tilt: float, zoom: float = 0.0, seconds: float,
                            timeout: float = 30.0) -> dict[str, Any]:
        """Continuous velocity move for ``seconds`` (max 10). Velocities in [-1, 1]."""
        body = {"camera": camera, "mode": "continuous", "pan": pan, "tilt": tilt,
                "zoom": zoom, "seconds": seconds}
        return self._json("POST", f"/v1/towers/{device_id}/ptz/move", json=body, timeout=timeout)

    def ptz_stop(self, device_id: str, *, camera: int = 1) -> None:
        self._json("POST", f"/v1/towers/{device_id}/ptz/stop", json={"camera": camera})

    def ptz_home(self, device_id: str, *, camera: int = 1) -> None:
        self._json("POST", f"/v1/towers/{device_id}/ptz/stop",
                   json={"camera": camera, "home": True})

    def ptz_status(self, device_id: str, *, camera: int = 1) -> PTZStatus:
        data = self._json("GET", f"/v1/towers/{device_id}/ptz/status",
                          params={"camera": camera})
        return PTZStatus.from_result(data.get("result", {}))

    # ── tower: media & telemetry ─────────────────────────────────────────────
    def snapshot(self, device_id: str, *, camera: int = 1, timeout: float = 30.0) -> bytes:
        """Capture a JPEG still frame from a camera. Returns raw JPEG bytes.
        Takes 1-4 s (the tower decodes one frame from its local RTSP stream)."""
        resp = self._request("GET", f"/v1/towers/{device_id}/snapshot/cam{camera}",
                             timeout=timeout)
        return resp.content

    def tower_status(self, device_id: str) -> dict[str, Any]:
        """Live watchdog sensor/health snapshot. Keys vary with the tower's
        enabled hardware; ``available: false`` means the tower is reachable
        but its watchdog status API is not running."""
        return self._json("GET", f"/v1/towers/{device_id}/status")

    def tower_streams(self, device_id: str) -> list[StreamPath]:
        data = self._json("GET", f"/v1/towers/{device_id}/streams")
        return [StreamPath.from_dict(p) for p in data.get("paths", [])]
