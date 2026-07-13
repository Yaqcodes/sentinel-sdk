import { errorFromResponse } from './errors.js';
import type {
  Customer,
  PlatformAlert,
  PtzMoveBody,
  PtzStatusResult,
  PtzStopBody,
  StatusResponse,
  StreamsResponse,
  Tower,
} from './models.js';

export interface SentinelClientOptions {
  apiKey?: string;
  /** Default per-request timeout in ms */
  timeout?: number;
  /** Custom fetch (tests, SSR) */
  fetch?: typeof fetch;
}

export class SentinelClient {
  private readonly base: string;
  private readonly apiKey?: string;
  private readonly timeout: number;
  private readonly fetchFn: typeof fetch;

  constructor(baseUrl: string, options: SentinelClientOptions = {}) {
    this.base = baseUrl.replace(/\/$/, '');
    this.apiKey = options.apiKey;
    this.timeout = options.timeout ?? 15_000;
    this.fetchFn = options.fetch ?? ((input, init) => globalThis.fetch(input, init));
  }

  private headers(extra?: HeadersInit): Headers {
    const h = new Headers(extra);
    if (!h.has('Accept')) h.set('Accept', 'application/json');
    if (this.apiKey) h.set('X-Kallon-Api-Key', this.apiKey);
    // ngrok free tier returns an HTML warning page (no CORS headers) unless this is set.
    if (this.base.includes('ngrok')) h.set('ngrok-skip-browser-warning', '1');
    return h;
  }

  private async request<T>(
    method: string,
    path: string,
    init: RequestInit & { timeout?: number } = {},
  ): Promise<T> {
    const ac = new AbortController();
    const ms = init.timeout ?? this.timeout;
    const timer = setTimeout(() => ac.abort(), ms);
    try {
      const res = await this.fetchFn(`${this.base}${path}`, {
        ...init,
        method,
        headers: this.headers(init.headers),
        signal: ac.signal,
      });
      if (res.status >= 400) {
        let body: unknown;
        try {
          body = await res.json();
        } catch {
          body = await res.text();
        }
        throw errorFromResponse(res.status, body);
      }
      if (res.status === 204) return undefined as T;
      const ct = res.headers.get('content-type') ?? '';
      if (ct.includes('application/json')) return (await res.json()) as T;
      return (await res.text()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // ── fleet ────────────────────────────────────────────────────────────────
  async listCustomers(): Promise<Customer[]> {
    const data = await this.request<{ customers: Customer[] }>('GET', '/v1/customers');
    return data.customers ?? [];
  }

  async getCustomer(customerId: string): Promise<Customer> {
    return this.request<Customer>('GET', `/v1/customers/${encodeURIComponent(customerId)}`);
  }

  async listCustomerTowers(customerId: string): Promise<Tower[]> {
    const data = await this.request<{ towers: Tower[] }>(
      'GET',
      `/v1/customers/${encodeURIComponent(customerId)}/towers`,
    );
    return data.towers ?? [];
  }

  async listTowers(status?: string): Promise<Tower[]> {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    const data = await this.request<{ towers: Tower[] }>('GET', `/v1/towers${q}`);
    return data.towers ?? [];
  }

  async getTower(deviceId: string): Promise<Tower> {
    return this.request<Tower>('GET', `/v1/towers/${encodeURIComponent(deviceId)}`);
  }

  // ── tower proxy ──────────────────────────────────────────────────────────
  async ptzMove(deviceId: string, body: PtzMoveBody): Promise<Record<string, unknown>> {
    return this.request('POST', `/v1/towers/${encodeURIComponent(deviceId)}/ptz/move`, {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      timeout: 30_000,
    });
  }

  async ptzStop(deviceId: string, body: PtzStopBody = {}): Promise<Record<string, unknown>> {
    return this.request('POST', `/v1/towers/${encodeURIComponent(deviceId)}/ptz/stop`, {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  async ptzStatus(deviceId: string, camera = 1): Promise<PtzStatusResult> {
    return this.request(
      'GET',
      `/v1/towers/${encodeURIComponent(deviceId)}/ptz/status?camera=${camera}`,
    );
  }

  async snapshot(deviceId: string, camera = 1): Promise<Blob> {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 30_000);
    try {
      const res = await this.fetchFn(
        `${this.base}/v1/towers/${encodeURIComponent(deviceId)}/snapshot/cam${camera}`,
        { headers: this.headers({ Accept: 'image/jpeg' }), signal: ac.signal },
      );
      if (!res.ok) {
        let body: unknown;
        try { body = await res.json(); } catch { body = null; }
        throw errorFromResponse(res.status, body);
      }
      return await res.blob();
    } finally {
      clearTimeout(timer);
    }
  }

  async towerStatus(deviceId: string): Promise<StatusResponse> {
    return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}/status`);
  }

  async towerStreams(deviceId: string): Promise<StreamsResponse> {
    return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}/streams`);
  }

  // ── alerts ───────────────────────────────────────────────────────────────
  async listAlerts(opts: {
    customerId?: string;
    deviceId?: string;
    limit?: number;
  } = {}): Promise<PlatformAlert[]> {
    const p = new URLSearchParams();
    if (opts.customerId) p.set('customer_id', opts.customerId);
    if (opts.deviceId) p.set('device_id', opts.deviceId);
    if (opts.limit != null) p.set('limit', String(opts.limit));
    const q = p.toString();
    const data = await this.request<{ alerts: PlatformAlert[] }>(
      'GET',
      `/v1/alerts${q ? `?${q}` : ''}`,
    );
    return data.alerts ?? [];
  }

  async listCustomerAlerts(customerId: string, limit = 100): Promise<PlatformAlert[]> {
    const data = await this.request<{ alerts: PlatformAlert[] }>(
      'GET',
      `/v1/customers/${encodeURIComponent(customerId)}/alerts?limit=${limit}`,
    );
    return data.alerts ?? [];
  }

  /** SSE URL for live alerts (use fetch-event-source or same-origin proxy for auth headers). */
  eventsUrl(customerId?: string): string {
    const p = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : '';
    return `${this.base}/v1/events${p}`;
  }
}
