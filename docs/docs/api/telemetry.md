---
id: telemetry
title: Telemetry (Status & Streams)
sidebar_position: 6
---

# Telemetry

Live sensor/health data and stream readiness, proxied from the tower's
watchdog and media server.

## Sensor & health snapshot

`GET /v1/towers/{device_id}/status`

```python
status = client.tower_status("kln_acme_000042")
```

```javascript
const status = await (await fetch(`${BASE}/v1/towers/kln_acme_000042/status`)).json();
```

```bash
curl -s $BASE/v1/towers/kln_acme_000042/status | jq
```

Response `200` — a snapshot of the watchdog's in-memory state. **Keys vary
with the tower's enabled hardware** (MPU-6050 accelerometer, reed switch,
light sensor, NVMe, temperature). Representative example:

```json
{
  "available": true,
  "device_id": "kln_acme_000042",
  "sensors": {
    "mpu6050": {"present": true, "last_delta_mg": 12.4},
    "reed": {"present": true, "open": false},
    "ldr": {"present": true, "bright": false}
  },
  "streams": {"cam1": {"ok": true}},
  "temperature_c": 46.2
}
```

:::note
`{"available": false, "error": "..."}` with HTTP 200 means the tower is
**reachable** but its watchdog status API is not running (it is optional on
some builds). This is different from `503 tower_offline`.
:::

## Stream readiness {#stream-readiness}

`GET /v1/towers/{device_id}/streams`

Whether each camera's RTSP rebroadcast path is live on the tower's media
server — check this before pulling RTSP or debugging snapshot failures.

```python
for path in client.tower_streams("kln_acme_000042"):
    print(path.name, "ready" if path.ready else "DOWN", f"{path.readers} readers")
```

```bash
curl -s $BASE/v1/towers/kln_acme_000042/streams | jq
```

Response `200`:

```json
{
  "available": true,
  "paths": [
    {"name": "cam1", "ready": true, "readers": 1, "source": "rtspSource"},
    {"name": "cam2", "ready": false, "readers": 0, "source": null}
  ]
}
```

`ready: false` usually means the camera itself is unreachable on the tower's
camera VLAN (power, cabling, or credentials).

## Alerts are push, not poll

Don't poll `/status` to detect tamper events — towers **push** signed alerts
within seconds of detection. See the [Alert Webhooks guide](../guides/alerts).
Use `/status` for dashboards and diagnostics.
