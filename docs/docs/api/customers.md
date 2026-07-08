---
id: customers
title: Customers
sidebar_position: 2
---

# Customers

A customer organization owns a dedicated WireGuard hub and an isolated VPN
subnet (`/24`). Towers belong to exactly one customer.

## List customers

`GET /v1/customers`

```python
customers = client.list_customers()
for c in customers:
    print(c.customer_id, c.display_name, c.vpn_subnet, c.status)
```

```javascript
const { customers } = await (await fetch(`${BASE}/v1/customers`)).json();
```

```bash
curl -s $BASE/v1/customers | jq
```

Response `200`:

```json
{
  "customers": [
    {
      "customer_id": "cust_acme",
      "display_name": "Acme Security",
      "vpn_subnet": "10.50.0.0/24",
      "gateway_id": "gw_acme",
      "gateway_endpoint": "203.0.113.42:51820",
      "gateway_public_key": "aGVsbG8...=",
      "hub_alert_url": "http://10.50.0.1:8080/alerts",
      "hub_provider": "lightsail",
      "hub_host_id": "ls-0abc123",
      "status": "active",
      "created_at": "2026-06-01T10:00:00"
    }
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `customer_id` | string | `cust_<slug>` |
| `vpn_subnet` | string | Customer's isolated WireGuard `/24` |
| `gateway_endpoint` | string \| null | Hub public `host:port` (WireGuard UDP) |
| `hub_alert_url` | string \| null | Where towers POST signed alerts |
| `hub_provider` | string | `lightsail` \| `manual` \| … |
| `status` | string | `pending_hub` \| `active` \| `suspended` |

Secrets (WireGuard private keys, HMAC keys) are **never** returned by any
endpoint.

## Get one customer

`GET /v1/customers/{customer_id}`

```python
customer = client.get_customer("cust_acme")
```

```bash
curl -s $BASE/v1/customers/cust_acme
```

`404 not_found` if unknown.

## List a customer's towers

`GET /v1/customers/{customer_id}/towers`

```python
towers = client.list_customer_towers("cust_acme")
```

```javascript
const { towers } = await (await fetch(`${BASE}/v1/customers/cust_acme/towers`)).json();
```

Response shape is identical to [Towers](towers#tower-object).
