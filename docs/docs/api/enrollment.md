---
id: enrollment
title: Enrollment (Tower First Boot)
sidebar_position: 7
---

# Enrollment

:::info
These endpoints are called **by towers**, not by integrators. They are
documented for completeness and for factory/ops tooling. Their error shape
is FastAPI's `{"detail": "..."}` (a pre-existing contract baked into factory
images), not the platform error envelope.
:::

On first boot in the field, a tower auto-enrolls: it presents its one-time
enrollment token, receives its VPN identity, brings up WireGuard, and
confirms. No human interaction.

```text
Tower ──POST /v1/enroll──────────► validates token, allocates VPN IP,
                                   adds WireGuard peer on the customer hub
      ◄─{vpn_ip, gateway, confirm_token}─
Tower ──WireGuard handshake──────► customer hub
Tower ──POST /v1/enroll/confirm──► marked active in the registry
```

## POST /v1/enroll

```json
{
  "device_id": "kln_acme_000042",
  "wg_public_key": "dG93ZXIuLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLi4uLg=",
  "enrollment_token": "enr_..."
}
```

`claim_code` may be sent instead of `device_id` (QR-label flow).

Response `200`:

```json
{
  "device_id": "kln_acme_000042",
  "vpn_ip": "10.50.0.2",
  "vpn_subnet": "10.50.0.0/24",
  "gateway_endpoint": "203.0.113.42:51820",
  "gateway_public_key": "aHVi...=",
  "alert_webhook_url": "http://10.50.0.1:8080/alerts",
  "confirm_token": "cnf_..."
}
```

| Status | Meaning |
|---|---|
| 401 | Wrong/expired enrollment token |
| 404 | Unknown device_id / claim_code |
| 409 | Customer hub not active or missing hub metadata |
| 422 | Malformed WireGuard public key or request |
| 502 | Hub peer-add failed (tower retries automatically) |

Enrollment is idempotent — re-enrolling with the same key returns the same
VPN IP and re-asserts the hub peer (self-healing after a hub rebuild).

## POST /v1/enroll/confirm

```json
{"device_id": "kln_acme_000042", "confirm_token": "cnf_...", "handshake_ok": true}
```

Marks the tower `active`. The confirm token is one-time.

## GET /healthz

Liveness probe for the control plane API: `{"status": "ok"}`.
