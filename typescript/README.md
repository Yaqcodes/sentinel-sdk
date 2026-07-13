# Sentinel SDK — TypeScript

Typed client for the Kallon Platform API (`/v1`).

```bash
npm install
npm run build
```

```typescript
import { SentinelClient } from '@sentinel/sdk';

const client = new SentinelClient('https://api.terra.example', {
  apiKey: process.env.KALLON_API_KEY,
});

const towers = await client.listCustomerTowers('cust_acme');
const jpeg = await client.snapshot('kln_acme_000001', 1);
```

See `docs/platform-api.md` in kallon-sentry for the full contract with JSON examples.
