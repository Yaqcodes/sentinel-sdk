"""Unit tests for SentinelClient against a mocked platform API."""
from __future__ import annotations

import json

import httpx
import pytest

from sentinel_sdk import (
    NotFoundError,
    PTZStatus,
    SentinelClient,
    TowerNotEnrolledError,
    TowerOfflineError,
    TransportError,
)

FAKE_JPEG = b"\xff\xd8\xff\xe0" + b"J" * 32 + b"\xff\xd9"

TOWER = {
    "device_id": "kln_acme_000042", "customer_id": "cust_acme", "group_id": None,
    "vpn_ip": "10.50.0.2", "wg_public_key": "K=", "status": "active",
    "acceptance_status": "pending", "manufactured_at": None,
    "enrolled_at": "2026-06-20T07:12:44", "shipped_at": None,
    "rtsp_base": "rtsp://10.50.0.2:8554",
}

CUSTOMER = {
    "customer_id": "cust_acme", "display_name": "Acme Security",
    "vpn_subnet": "10.50.0.0/24", "gateway_endpoint": "203.0.113.42:51820",
    "gateway_public_key": "H=", "gateway_id": "gw_acme",
    "hub_alert_url": "http://10.50.0.1:8080/alerts", "hub_provider": "lightsail",
    "hub_host_id": None, "status": "active", "created_at": "2026-06-01T10:00:00",
}


def _handler(request: httpx.Request) -> httpx.Response:
    path, method = request.url.path, request.method

    if path == "/v1/customers" and method == "GET":
        return httpx.Response(200, json={"customers": [CUSTOMER]})
    if path == "/v1/customers/cust_acme":
        return httpx.Response(200, json=CUSTOMER)
    if path == "/v1/customers/cust_nope":
        return httpx.Response(404, json={"error": {"code": "not_found", "message": "unknown customer"}})
    if path == "/v1/towers" and method == "GET":
        return httpx.Response(200, json={"towers": [TOWER]})
    if path == "/v1/towers" and method == "POST":
        body = json.loads(request.content)
        return httpx.Response(201, json={
            "device_id": f"kln_acme_{body['serial']:06d}", "customer_id": body["customer_id"],
            "claim_code": "clm_x", "enrollment_token": "enr_y",
        })
    if path == "/v1/towers/kln_acme_000042" and method == "GET":
        return httpx.Response(200, json=TOWER)
    if path == "/v1/towers/kln_acme_000042/ptz/move":
        return httpx.Response(200, json={"ok": True, "result": {"ok": True, "round_trip_ms": 42.0}})
    if path == "/v1/towers/kln_acme_000042/ptz/stop":
        return httpx.Response(200, json={"ok": True, "result": {}})
    if path == "/v1/towers/kln_acme_000042/ptz/status":
        return httpx.Response(200, json={"ok": True, "result": {"pan": 0.5, "tilt": -0.2, "zoom": 0.1}})
    if path == "/v1/towers/kln_acme_000042/snapshot/cam1":
        return httpx.Response(200, content=FAKE_JPEG, headers={"content-type": "image/jpeg"})
    if path == "/v1/towers/kln_acme_000042/status":
        return httpx.Response(200, json={"available": True, "temperature_c": 45.0})
    if path == "/v1/towers/kln_acme_000042/streams":
        return httpx.Response(200, json={"available": True,
                                         "paths": [{"name": "cam1", "ready": True, "readers": 2}]})
    if path == "/v1/towers/kln_acme_000077/status":
        return httpx.Response(503, json={"error": {
            "code": "tower_offline", "message": "tower did not respond",
            "device_id": "kln_acme_000077"}})
    if path == "/v1/towers/kln_acme_000088/status":
        return httpx.Response(409, json={"error": {
            "code": "tower_not_enrolled", "message": "no VPN IP yet",
            "device_id": "kln_acme_000088"}})
    return httpx.Response(404, json={"error": {"code": "not_found", "message": path}})


@pytest.fixture
def client() -> SentinelClient:
    return SentinelClient("https://api.test", transport=httpx.MockTransport(_handler))


def test_list_customers(client):
    customers = client.list_customers()
    assert len(customers) == 1
    assert customers[0].customer_id == "cust_acme"
    assert customers[0].vpn_subnet == "10.50.0.0/24"


def test_get_customer_not_found(client):
    with pytest.raises(NotFoundError) as e:
        client.get_customer("cust_nope")
    assert e.value.status_code == 404
    assert e.value.code == "not_found"


def test_get_tower_and_rtsp_url(client):
    tower = client.get_tower("kln_acme_000042")
    assert tower.vpn_ip == "10.50.0.2"
    assert tower.rtsp_url(2) == "rtsp://10.50.0.2:8554/cam2"


def test_register_tower(client):
    reg = client.register_tower("cust_acme", 43)
    assert reg.device_id == "kln_acme_000043"
    assert reg.enrollment_token == "enr_y"


def test_ptz_roundtrip(client):
    result = client.ptz_move("kln_acme_000042", camera=1, pan=0.5, tilt=-0.2)
    assert result["result"]["round_trip_ms"] == 42.0
    client.ptz_stop("kln_acme_000042")
    status = client.ptz_status("kln_acme_000042")
    assert status == PTZStatus(pan=0.5, tilt=-0.2, zoom=0.1)


def test_snapshot(client):
    jpeg = client.snapshot("kln_acme_000042", camera=1)
    assert jpeg == FAKE_JPEG
    assert jpeg.startswith(b"\xff\xd8")


def test_tower_status_and_streams(client):
    status = client.tower_status("kln_acme_000042")
    assert status["temperature_c"] == 45.0
    paths = client.tower_streams("kln_acme_000042")
    assert paths[0].name == "cam1" and paths[0].ready is True


def test_tower_offline(client):
    with pytest.raises(TowerOfflineError) as e:
        client.tower_status("kln_acme_000077")
    assert e.value.status_code == 503
    assert e.value.device_id == "kln_acme_000077"


def test_tower_not_enrolled(client):
    with pytest.raises(TowerNotEnrolledError):
        client.tower_status("kln_acme_000088")


def test_transport_error():
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    client = SentinelClient("https://api.test", transport=httpx.MockTransport(boom))
    with pytest.raises(TransportError):
        client.list_towers()


def test_api_key_header_sent():
    seen = {}

    def capture(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers.get("X-Kallon-Api-Key")
        return httpx.Response(200, json={"towers": []})

    client = SentinelClient("https://api.test", api_key="k123",
                            transport=httpx.MockTransport(capture))
    client.list_towers()
    assert seen["key"] == "k123"
