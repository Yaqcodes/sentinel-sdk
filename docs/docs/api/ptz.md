---
id: ptz
title: PTZ Control
sidebar_position: 4
---

# PTZ Control

Pan/tilt/zoom control for ONVIF cameras on a tower. Commands are proxied by
the control plane over the VPN to the tower's local PTZ daemon.

**Coordinate space (ONVIF normalized):** pan and tilt in `[-1, 1]`, zoom in
`[0, 1]`. Continuous moves use velocities in `[-1, 1]`.

**Latency:** one VPN round trip plus camera execution. Absolute moves
block until the camera confirms position — budget **1–2 seconds** (Dahua
ONVIF ceiling is ~1.6 s p95). Set client timeouts accordingly.

## Move (absolute)

`POST /v1/towers/{device_id}/ptz/move`

**① Python · `SentinelClient`**

```python
result = client.ptz_move("kln_acme_000042", camera=1, pan=0.5, tilt=-0.2, zoom=0.0)
print(result["result"]["round_trip_ms"])
```

**② JavaScript · `fetch`**

```javascript
const res = await fetch(`${BASE}/v1/towers/kln_acme_000042/ptz/move`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ camera: 1, mode: "absolute", pan: 0.5, tilt: -0.2, zoom: 0.0 }),
});
```

**③ curl · shell**

```bash
curl -s -X POST $BASE/v1/towers/kln_acme_000042/ptz/move \
  -H "Content-Type: application/json" \
  -d '{"camera": 1, "mode": "absolute", "pan": 0.5, "tilt": -0.2}'
```

Request fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `camera` | int | no (default 1) | 1-based camera index |
| `mode` | string | no (default `absolute`) | `absolute` \| `continuous` |
| `pan`, `tilt` | float | yes | position (absolute) or velocity (continuous) |
| `zoom` | float | absolute: no · continuous: yes | |
| `seconds` | float | continuous only | max 10 |

Response `200`:

```json
{"ok": true, "result": {"ok": true, "round_trip_ms": 1240.5}}
```

## Move (continuous)

Same endpoint, `mode: "continuous"` — moves at the given velocity for
`seconds`, then stops:

**① Python · `SentinelClient`**

```python
client.ptz_move_continuous("kln_acme_000042", camera=1,
                           pan=0.3, tilt=0.0, zoom=0.0, seconds=0.5)
```

**③ curl · shell**

```bash
curl -s -X POST $BASE/v1/towers/kln_acme_000042/ptz/move \
  -H "Content-Type: application/json" \
  -d '{"camera": 1, "mode": "continuous", "pan": 0.3, "tilt": 0, "zoom": 0, "seconds": 0.5}'
```

## Stop / Home

`POST /v1/towers/{device_id}/ptz/stop`

**① Python · `SentinelClient`**

```python
client.ptz_stop("kln_acme_000042", camera=1)
client.ptz_home("kln_acme_000042", camera=1)   # {"home": true}
```

**③ curl · shell**

```bash
curl -s -X POST $BASE/v1/towers/kln_acme_000042/ptz/stop \
  -H "Content-Type: application/json" -d '{"camera": 1}'
```

## Position

`GET /v1/towers/{device_id}/ptz/status?camera=1`

**① Python · `SentinelClient`**

```python
pos = client.ptz_status("kln_acme_000042", camera=1)
print(pos.pan, pos.tilt, pos.zoom)
```

**③ curl · shell**

```bash
curl -s "$BASE/v1/towers/kln_acme_000042/ptz/status?camera=1"
```

Response `200`:

```json
{"ok": true, "result": {"pan": 0.5, "tilt": -0.2, "zoom": 0.0}}
```

## Failure modes

| Error | Typical cause |
|---|---|
| `422 invalid_request` | Bad mode / missing fields — rejected before the VPN round trip |
| `409 tower_not_enrolled` | Tower has no VPN IP yet |
| `503 tower_offline` | Tunnel down or tower rebooting |
| `502 tower_error` | PTZ daemon down, wrong ONVIF credentials, or camera unreachable on the camera VLAN — the response includes the daemon's error object |
