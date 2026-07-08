# Sentinel SDK

Official Python SDK and developer reference for the **Kallon Sentry Tower**
platform (Terra Industries) — sovereign edge surveillance: live RTSP over
WireGuard, PTZ control, snapshots, sensor telemetry, and HMAC-signed alerts.

The SDK talks to **one base URL** — the Terra control plane platform API.
Tower-specific operations (PTZ, snapshots, sensors) are proxied by the
control plane over the VPN; your code never connects to a tower directly.

## Install

```bash
pip install git+https://github.com/Yaqcodes/sentinel-sdk
# (PyPI publication pending — see docs)
```

## Quick start

```python
from sentinel_sdk import SentinelClient

client = SentinelClient("https://api.terra.example")  # api_key="..." when auth lands

# Fleet
for tower in client.list_towers():
    print(tower.device_id, tower.status, tower.rtsp_base)

# PTZ (proxied over VPN — expect 1-2 s round trip)
client.ptz_move("kln_acme_000042", camera=1, pan=0.5, tilt=-0.2)

# Snapshot (JPEG bytes)
open("frame.jpg", "wb").write(client.snapshot("kln_acme_000042", camera=1))

# Sensor / health telemetry
print(client.tower_status("kln_acme_000042"))
```

## Verify alert webhooks

```python
from sentinel_sdk import AlertVerifier

verifier = AlertVerifier.from_key_file("/etc/kallon/alert.key")

def webhook_handler(raw_body: bytes, signature_header: str):
    if not verifier.verify(raw_body, signature_header):
        return 401
    alert = verifier.parse(raw_body)
    print(alert.alert_type, alert.severity, alert.details)
```

## Error handling

```python
from sentinel_sdk import SentinelError, TowerOfflineError

try:
    client.snapshot("kln_acme_000042")
except TowerOfflineError as e:
    print(f"tower {e.device_id} is offline — VPN down or rebooting")
except SentinelError as e:
    print(f"SDK error: {e}")
```

## Documentation

The full developer reference (API docs with Python/JavaScript/curl examples,
integration guides, and the tower bring-up guide) is a Docusaurus site under
[`docs/`](docs/):

```bash
cd docs && npm install && npm run start
```

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## Notes

- **Auth:** the platform API does not enforce authentication yet. Pass
  `api_key=` anyway — the client sends `X-Kallon-Api-Key` so your code needs
  no changes when enforcement lands.
- **Live video:** RTSP cannot be HTTP-proxied. Live streams require WireGuard
  peer membership in the customer subnet — see the RTSP guide in the docs.
  Use `snapshot()` for HTTP-friendly still frames.
