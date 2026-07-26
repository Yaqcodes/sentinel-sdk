---
id: alerts-api
title: Alerts (Platform API)
sidebar_position: 7
---

# Alerts — ingest, history, and SSE

Tower events reach the control plane via hub forward. Configure each customer
hub:

```text
ALERT_FORWARD_URL=https://api.terra.example/v1/alerts/ingest
ALERT_INGEST_TOKEN=<same as KALLON_ALERT_INGEST_TOKEN>
```

## Ingest

`POST /v1/alerts/ingest`

Request (verbatim tower alert body):

```json
{
  "device_id": "kln_acme_000001",
  "timestamp_utc": "2026-07-13T10:31:12Z",
  "nonce": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "alert_type": "tamper_door_open",
  "severity": "critical",
  "details": {
    "gpio_pin": 31,
    "level": "HIGH",
    "boot_state": true
  }
}
```

Response `201`:

```json
{
  "status": "accepted",
  "alert": {
    "device_id": "kln_acme_000001",
    "customer_id": "cust_acme",
    "alert_type": "tamper_door_open",
    "kind": "tamper_door_open",
    "severity": "critical",
    "timestamp_utc": "2026-07-13T10:31:12Z",
    "nonce": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "details": {"gpio_pin": 31, "level": "HIGH", "boot_state": true},
    "received_utc": "2026-07-13T10:31:12Z"
  }
}
```

## History

`GET /v1/customers/cust_acme/alerts?limit=50`

```json
{
  "alerts": [
    {
      "device_id": "kln_acme_000001",
      "customer_id": "cust_acme",
      "alert_type": "wind_high",
      "kind": "wind_high",
      "severity": "warning",
      "timestamp_utc": "2026-07-13T10:28:04Z",
      "nonce": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "details": {"kmh": 34, "gust": 41, "trip": 30},
      "received_utc": "2026-07-13T10:28:05Z"
    }
  ]
}
```

## Live updates (SSE)

`GET /v1/events?customer_id=cust_acme`

Each SSE message:

```text
data: {"device_id":"kln_acme_000001","customer_id":"cust_acme","alert_type":"stream_fail","severity":"warning","timestamp_utc":"2026-07-13T10:35:00Z","nonce":"9b8c7d6e-5f4a-3210-9876-543210fedcba","details":{"url":"rtsp://127.0.0.1:8554/cam3"},"received_utc":"2026-07-13T10:35:01Z"}

```

**TypeScript · `@sentinel/sdk`** (same operations as ①, typed client)

```typescript
const alerts = await client.listCustomerAlerts("cust_acme");
const url = client.eventsUrl("cust_acme"); // use same-origin proxy for auth headers
```

See [Alert Webhooks guide](../guides/alerts) for the tower→hub HMAC contract.
