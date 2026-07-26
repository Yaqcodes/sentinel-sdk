---
id: towers
title: Towers
sidebar_position: 3
---

# Towers

A tower is a Jetson-based edge unit running cameras, sensors, a WireGuard
tunnel, and the local services the platform proxies to.

## Tower object {#tower-object}

```json
{
  "device_id": "kln_acme_000042",
  "customer_id": "cust_acme",
  "group_id": null,
  "vpn_ip": "10.50.0.2",
  "wg_public_key": "dG93ZXI...=",
  "status": "active",
  "acceptance_status": "pending",
  "manufactured_at": "2026-06-10T09:00:00",
  "enrolled_at": "2026-06-20T07:12:44",
  "shipped_at": null,
  "rtsp_base": "rtsp://10.50.0.2:8554"
}
```

| Field | Type | Notes |
|---|---|---|
| `device_id` | string | `kln_<slug>_<6 digits>` |
| `vpn_ip` | string \| null | Null until first-boot enrollment completes |
| `status` | string | `manufactured` → `enrolled` → `active` (or `suspended`) |
| `rtsp_base` | string \| null | Derived; camera paths are `cam1..camN`. Requires VPN peer membership — see the [RTSP guide](../guides/rtsp) |
| `acceptance_status`, `shipped_at` | | Present in the schema but not yet written by the factory flow — treat as best-effort |

`claim_code` and enrollment tokens are never returned.

## List all towers

`GET /v1/towers` — optional `?status=active` filter.

**① Python · `SentinelClient`**

```python
active = client.list_towers(status="active")
```

**③ curl · shell**

```bash
curl -s "$BASE/v1/towers?status=active"
```

## Get one tower

`GET /v1/towers/{device_id}`

**① Python · `SentinelClient`**

```python
tower = client.get_tower("kln_acme_000042")
print(tower.rtsp_url(1))   # rtsp://10.50.0.2:8554/cam1
```

**② JavaScript · `fetch`**

```javascript
const tower = await (await fetch(`${BASE}/v1/towers/kln_acme_000042`)).json();
```

`404 not_found` if unknown.

## Register a tower (factory)

`POST /v1/towers`

:::danger Terra ops only
This returns a **one-time** plaintext `enrollment_token` (the registry stores
only its hash). Until API auth is enforced, this endpoint must not be exposed
beyond the Terra ops network.
:::

**① Python · `SentinelClient`**

```python
reg = client.register_tower("cust_acme", serial=43)
print(reg.device_id)          # kln_acme_000043
print(reg.enrollment_token)   # enr_... — store securely, shown once
print(reg.claim_code)         # clm_... — goes on the QR label
```

**③ curl · shell**

```bash
curl -s -X POST $BASE/v1/towers \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "cust_acme", "serial": 43}'
```

Response `201`:

```json
{
  "device_id": "kln_acme_000043",
  "customer_id": "cust_acme",
  "claim_code": "clm_8f3kLmNpQrStUvWxYz12",
  "enrollment_token": "enr_A1b2C3..."
}
```

| Error | Meaning |
|---|---|
| `404 not_found` | Unknown customer |
| `409 conflict` | Serial already registered for this customer |
| `422 invalid_request` | Serial out of range (0–999999) |
