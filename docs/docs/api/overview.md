---
id: overview
title: Overview & Conventions
sidebar_position: 1
---

# API Overview

Base URL: your Terra control plane, e.g. `https://api.terra.example`.
All endpoints are under `/v1`. Bodies are JSON except snapshots
(`image/jpeg`). A machine-readable OpenAPI spec is served at
`GET /openapi.json`.

## Endpoint families

| Family | Backed by | Latency |
|---|---|---|
| **Fleet** — customers, towers | Postgres registry | milliseconds |
| **Tower proxy** — PTZ, snapshot, status, streams | Proxied over WireGuard to the tower | +50–100 ms VPN, PTZ ~1–2 s, snapshot 1–4 s |
| **Enrollment** — tower first boot | Registry + hub automation | used by towers, not integrators |

## Identifiers

| Entity | Format | Example |
|---|---|---|
| Customer | `cust_<slug>` | `cust_acme` |
| Tower | `kln_<slug>_<6 digits>` | `kln_acme_000042` |
| Camera | 1-based integer per tower | `1` |

## Errors {#errors}

All fleet and proxy endpoints return errors in one envelope:

```json
{
  "error": {
    "code": "tower_offline",
    "message": "tower did not respond (ConnectTimeout) — VPN tunnel down or tower rebooting",
    "device_id": "kln_acme_000042"
  }
}
```

| HTTP | `code` | Meaning | SDK exception |
|---|---|---|---|
| 401 | `unauthorized` | Missing/invalid API key | `AuthError` |
| 404 | `not_found` | Unknown customer, tower, or camera | `NotFoundError` |
| 409 | `tower_not_enrolled` | Tower registered but not yet enrolled (no VPN IP) | `TowerNotEnrolledError` |
| 422 | `invalid_request` | Malformed body/params | `InvalidRequestError` |
| 502 | `tower_error` | Tower reached, but its gateway reported a failure | `TowerError` |
| 503 | `tower_offline` | Tower unreachable over VPN | `TowerOfflineError` |
| 503 | `registry_unavailable` | Fleet database unreachable | `APIError` |

Python:

```python
from sentinel_sdk import SentinelClient, TowerOfflineError, SentinelError

client = SentinelClient("https://api.terra.example")
try:
    status = client.tower_status("kln_acme_000042")
except TowerOfflineError as e:
    schedule_retry(e.device_id)      # tower is rebooting or link is down
except SentinelError as e:
    log.error("platform API error: %s", e)
```

JavaScript:

```javascript
const res = await fetch(`${BASE}/v1/towers/kln_acme_000042/status`);
if (!res.ok) {
  const { error } = await res.json();
  if (error.code === "tower_offline") scheduleRetry(error.device_id);
  else throw new Error(`${error.code}: ${error.message}`);
}
```

## Retry guidance

- `tower_offline` (503) — retry with backoff; towers ride Wi-Fi/LTE and a
  30-second WireGuard watchdog restarts stale tunnels automatically.
- `tower_error` (502) — inspect the message; usually a camera-side fault.
- 4xx — do not retry without changing the request.

## Versioning

Breaking changes bump the path version (`/v1` → `/v2`). Additive fields may
appear in responses at any time — ignore keys you don't recognize (the
Python SDK does this automatically).
