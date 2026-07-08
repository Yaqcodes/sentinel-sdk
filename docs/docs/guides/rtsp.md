---
id: rtsp
title: Live Video (RTSP)
sidebar_position: 2
---

# Consuming Live Video

Live video is standard **RTSP over TCP**, served by each tower and reachable
**only over the customer's WireGuard VPN**. RTSP is not HTTP and cannot be
proxied through the platform API — this is the one surface that requires
network-level access.

:::caution
Your consumer (dashboard backend, relay, NVR) must be a WireGuard peer in the
customer subnet. The `x.x.x.10` address in each subnet is reserved for this
NOC/consumer role. If you only need still frames, use the
[Snapshot API](../api/snapshot) instead — it is plain HTTPS.
:::

## Stream URLs

```text
rtsp://<tower-vpn-ip>:8554/cam<n>
```

- `<tower-vpn-ip>` — from the [Tower object](../api/towers#tower-object)
  (`vpn_ip`, or use the derived `rtsp_base`).
- `<n>` — 1-based camera index.
- Transport: **TCP** (`-rtsp_transport tcp`). Codec: H.264 recommended
  (H.265 streams work over RTSP but many browser toolchains cannot decode
  them — set camera substreams to H.264 at provisioning).

```python
tower = client.get_tower("kln_acme_000042")
url = tower.rtsp_url(1)          # rtsp://10.50.0.2:8554/cam1
```

## Probe / consume

```bash
# Verify connectivity from your VPN peer first
nc -zv 10.50.0.2 8554                        # Linux
Test-NetConnection 10.50.0.2 -Port 8554      # Windows

# Inspect the stream
ffprobe -rtsp_transport tcp rtsp://10.50.0.2:8554/cam1

# Watch
ffplay -rtsp_transport tcp rtsp://10.50.0.2:8554/cam1

# Re-serve to browsers as HLS (example relay)
ffmpeg -rtsp_transport tcp -i rtsp://10.50.0.2:8554/cam1 \
  -c:v copy -f hls -hls_time 2 -hls_list_size 5 /var/www/hls/cam1.m3u8
```

Python (OpenCV):

```python
import cv2

cap = cv2.VideoCapture("rtsp://10.50.0.2:8554/cam1", cv2.CAP_FFMPEG)
ok, frame = cap.read()
```

## Before you debug the player

1. `GET /v1/towers/{device_id}/streams` — is the path `ready` on the tower?
2. Can you reach TCP `8554` on the tower VPN IP from your peer?
3. If ping works but TCP fails, the customer hub is missing its
   wg0→wg0 forwarding rule (Terra ops: `kallon-gateway-ensure-forwarding.sh`
   on the hub).

## Future

A platform-hosted transcoding relay (HLS/WebRTC without VPN membership) is
on the roadmap but not committed. Design integrations against RTSP + the
snapshot API for now.
