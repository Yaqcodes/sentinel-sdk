---
id: alerts
title: Alert Webhooks
sidebar_position: 1
---

# Receiving & Verifying Alerts

Towers detect events (tamper, stream failure, temperature, light intrusion)
and push **HMAC-SHA256-signed JSON** to the customer hub. The hub forwards
verified alerts to the control plane (`POST /v1/alerts/ingest`). Customer
dashboards consume history via `GET /v1/alerts` or live updates via
`GET /v1/events` (SSE). See [Alerts API](../api/alerts-api).

For custom ingest (bypassing the platform), verify signatures yourself as
below. Alerts are push — you never poll tower status for events.

## The alert payload

```json
{
  "device_id": "kln_acme_000042",
  "timestamp_utc": "2026-07-08T14:30:00Z",
  "nonce": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "alert_type": "tamper_impact",
  "severity": "critical",
  "details": {"axis_mg": 312, "threshold_mg": 150}
}
```

| Field | Notes |
|---|---|
| `alert_type` | `tamper_impact`, `enclosure_open`, `stream_fail`, `temp_high`, `temp_clear`, `light_change`, … |
| `severity` | `info` \| `warning` \| `critical` |
| `nonce` | UUID v4, unique per POST |
| `details` | Type-specific context (optional) |

Delivery is **at-least-once** with a 60-second dedup window per alert type on
the tower and 3 retries with backoff. Deduplicate on
`(device_id, alert_type, timestamp_utc, nonce)`.

## The signature

Every POST carries:

```text
X-Kallon-Signature: sha256=<hex>
```

where `<hex> = HMAC_SHA256(key = alert.key, message = raw request body)`.
The canonical body is compact JSON with sorted keys — **always verify the
raw bytes you received**, never a re-parsed/re-serialized copy. Compare in
constant time; reject mismatches with HTTP 401.

## Verify — Python (SDK)

```python
from sentinel_sdk import AlertVerifier

verifier = AlertVerifier.from_key_file("/etc/kallon/alert.key")

# FastAPI example
from fastapi import FastAPI, Request, Response
app = FastAPI()

@app.post("/alerts")
async def alerts(request: Request):
    raw = await request.body()
    if not verifier.verify(raw, request.headers.get("X-Kallon-Signature", "")):
        return Response(status_code=401)
    alert = verifier.parse(raw)
    if alert.severity == "critical":
        page_oncall(alert)
    return {"status": "accepted"}
```

## Verify — JavaScript (Node)

```javascript
const crypto = require("crypto");
const fs = require("fs");

const KEY = fs.readFileSync("/etc/kallon/alert.key").toString().trim();

function verifyAlert(rawBody, signatureHeader) {
  const expected = crypto.createHmac("sha256", KEY).update(rawBody).digest("hex");
  const provided = (signatureHeader || "").replace(/^sha256=/, "");
  if (provided.length !== expected.length) return false;
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(provided));
}

// Express: capture the RAW body — do not verify a re-serialized req.body!
app.post("/alerts", express.raw({ type: "application/json" }), (req, res) => {
  if (!verifyAlert(req.body, req.headers["x-kallon-signature"])) {
    return res.sendStatus(401);
  }
  const alert = JSON.parse(req.body);
  res.json({ status: "accepted" });
});
```

## Test with curl

Produce a signed test POST against your endpoint:

```bash
KEY=$(cat /etc/kallon/alert.key)
BODY='{"alert_type":"stream_fail","details":{},"device_id":"kln_test_000001","nonce":"11111111-1111-4111-8111-111111111111","severity":"warning","timestamp_utc":"2026-07-08T12:00:00Z"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$KEY" -hex | awk '{print $2}')

curl -s -X POST http://localhost:8080/alerts \
  -H "Content-Type: application/json" \
  -H "X-Kallon-Signature: sha256=$SIG" \
  -d "$BODY"
```

(Note the body above is already compact JSON with sorted keys — the
canonical form.)

## Common mistakes

| Symptom | Cause |
|---|---|
| Every alert rejected 401 | Verifying a re-serialized body instead of the raw bytes (key order/whitespace changed) |
| Intermittent 401 | `alert.key` differs between tower and your service (trailing newline counts!) |
| Duplicate alerts processed | Not deduplicating on the idempotency key — delivery is at-least-once |
