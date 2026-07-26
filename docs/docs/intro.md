---
id: intro
title: Quick Start
sidebar_position: 1
slug: /
---

# Sentinel SDK — Quick Start

The **Kallon Sentry Tower** platform gives you programmatic access to a fleet
of edge surveillance towers: fleet metadata, PTZ camera control, JPEG
snapshots, live sensor telemetry, RTSP video, and HMAC-signed alerts.

Everything goes through **one base URL** — the Terra control plane platform
API. Tower-specific operations are proxied by the control plane over an
encrypted WireGuard VPN to the tower. Your code never connects to a tower
directly.

```text
Your app ──HTTPS──► Control plane API ──WireGuard VPN──► Sentry Tower
                        │
                        └── Postgres fleet registry
```

## 1. Install the SDK (Python)

```bash
pip install git+https://github.com/Yaqcodes/sentinel-sdk
```

Every API reference page labels examples **① Python · `SentinelClient`**, **②
JavaScript · `fetch`**, and **③ curl · shell** — see [API Overview](api/overview#code-examples-three-languages).

## 2. First API call

**① Python · `SentinelClient`**

```python
from sentinel_sdk import SentinelClient

client = SentinelClient("https://api.terra.example")

for tower in client.list_towers():
    print(tower.device_id, tower.status, tower.vpn_ip)
```

**② JavaScript · `fetch`**

```javascript
const res = await fetch("https://api.terra.example/v1/towers");
const { towers } = await res.json();
towers.forEach(t => console.log(t.device_id, t.status, t.vpn_ip));
```

**③ curl · shell**

```bash
curl -s https://api.terra.example/v1/towers | jq '.towers[] | {device_id, status}'
```

## 3. Move a camera and grab a frame

**① Python · `SentinelClient`**

```python
client.ptz_move("kln_acme_000042", camera=1, pan=0.5, tilt=-0.2)

jpeg = client.snapshot("kln_acme_000042", camera=1)
open("frame.jpg", "wb").write(jpeg)
```

PTZ and snapshot calls cross the VPN and wait on the camera — budget 1–4
seconds, and handle [`TowerOfflineError`](api/overview#errors).

## 4. Receive alerts

Towers push HMAC-signed alerts (tamper, stream failure, temperature…) to
your webhook. Verify each one with the shared key:

**① Python · `SentinelClient`**

```python
from sentinel_sdk import AlertVerifier

verifier = AlertVerifier.from_key_file("/etc/kallon/alert.key")
if verifier.verify(raw_body, request.headers["X-Kallon-Signature"]):
    alert = verifier.parse(raw_body)
```

Full walkthrough: [Alert Webhooks guide](guides/alerts).

## Authentication

:::caution
The platform API does **not enforce authentication yet**. Pass
`api_key="..."` to `SentinelClient` anyway (sent as `X-Kallon-Api-Key`) so
your integration needs zero changes when enforcement lands. Until then the
API must only be reachable from trusted networks.
:::

## What's where

| I want to… | Go to |
|---|---|
| Understand conventions, errors, versioning | [API Overview](api/overview) |
| List customers and towers | [Customers](api/customers) · [Towers](api/towers) |
| Control a PTZ camera | [PTZ Control](api/ptz) |
| Capture a still image | [Snapshots](api/snapshot) |
| Read sensors / stream health | [Telemetry](api/telemetry) |
| Consume live video | [RTSP guide](guides/rtsp) |
| Verify alert webhooks | [Alerts guide](guides/alerts) |
| Commission a new tower | [Tower Bring-Up guide](guides/tower-bring-up) |
