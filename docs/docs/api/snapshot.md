---
id: snapshot
title: Snapshots
sidebar_position: 5
---

# Snapshots

Capture a single JPEG still frame from any camera — the HTTP-friendly
alternative to RTSP for thumbnails, alert context images, and periodic
captures.

On the tower, a frame is decoded from the local RTSP rebroadcast with
ffmpeg. Expect **1–4 seconds** end to end.

## Capture a frame

`GET /v1/towers/{device_id}/snapshot/cam{n}`

Returns `200` with `Content-Type: image/jpeg` (raw JPEG bytes).

```python
jpeg = client.snapshot("kln_acme_000042", camera=1)
with open("frame.jpg", "wb") as f:
    f.write(jpeg)
```

```javascript
const res = await fetch(`${BASE}/v1/towers/kln_acme_000042/snapshot/cam1`);
if (!res.ok) throw new Error((await res.json()).error.message);
const blob = await res.blob();           // display: URL.createObjectURL(blob)
```

```bash
curl -s -o frame.jpg $BASE/v1/towers/kln_acme_000042/snapshot/cam1
```

## Errors

| Error | Meaning |
|---|---|
| `404 not_found` | Camera index out of range for this tower |
| `409 tower_not_enrolled` | Tower has no VPN IP yet |
| `503 tower_offline` | Tunnel down or tower rebooting |
| `502 tower_error` | ffmpeg failed on the tower — usually the camera stream is down (check [Telemetry → streams](telemetry#stream-readiness)) |

## Pattern: alert context image

Grab a frame when an alert arrives to attach visual context:

```python
def on_alert(alert):
    if alert.severity == "critical":
        try:
            jpeg = client.snapshot(alert.device_id, camera=1)
            store_evidence(alert.idempotency_key, jpeg)
        except SentinelError:
            pass  # tower may be offline during a tamper event — alert still stands
```
