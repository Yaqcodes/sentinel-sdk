import { errorFromResponse } from './errors.js';
export class SentinelClient {
    base;
    apiKey;
    timeout;
    fetchFn;
    constructor(baseUrl, options = {}) {
        this.base = baseUrl.replace(/\/$/, '');
        this.apiKey = options.apiKey;
        this.timeout = options.timeout ?? 15_000;
        this.fetchFn = options.fetch ?? ((input, init) => globalThis.fetch(input, init));
    }
    headers(extra) {
        const h = new Headers(extra);
        if (!h.has('Accept'))
            h.set('Accept', 'application/json');
        if (this.apiKey)
            h.set('X-Kallon-Api-Key', this.apiKey);
        // ngrok free tier returns an HTML warning page (no CORS headers) unless this is set.
        if (this.base.includes('ngrok'))
            h.set('ngrok-skip-browser-warning', '1');
        return h;
    }
    async request(method, path, init = {}) {
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
                let body;
                try {
                    body = await res.json();
                }
                catch {
                    body = await res.text();
                }
                throw errorFromResponse(res.status, body);
            }
            if (res.status === 204)
                return undefined;
            const ct = res.headers.get('content-type') ?? '';
            if (ct.includes('application/json'))
                return (await res.json());
            return (await res.text());
        }
        finally {
            clearTimeout(timer);
        }
    }
    // ── fleet ────────────────────────────────────────────────────────────────
    async listCustomers() {
        const data = await this.request('GET', '/v1/customers');
        return data.customers ?? [];
    }
    async getCustomer(customerId) {
        return this.request('GET', `/v1/customers/${encodeURIComponent(customerId)}`);
    }
    async listCustomerTowers(customerId) {
        const data = await this.request('GET', `/v1/customers/${encodeURIComponent(customerId)}/towers`);
        return data.towers ?? [];
    }
    async listTowers(status) {
        const q = status ? `?status=${encodeURIComponent(status)}` : '';
        const data = await this.request('GET', `/v1/towers${q}`);
        return data.towers ?? [];
    }
    async getTower(deviceId) {
        return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}`);
    }
    // ── tower proxy ──────────────────────────────────────────────────────────
    async ptzMove(deviceId, body) {
        return this.request('POST', `/v1/towers/${encodeURIComponent(deviceId)}/ptz/move`, {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            timeout: 30_000,
        });
    }
    async ptzStop(deviceId, body = {}) {
        return this.request('POST', `/v1/towers/${encodeURIComponent(deviceId)}/ptz/stop`, {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    }
    async ptzStatus(deviceId, camera = 1) {
        return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}/ptz/status?camera=${camera}`);
    }
    async snapshot(deviceId, camera = 1) {
        const ac = new AbortController();
        const timer = setTimeout(() => ac.abort(), 30_000);
        try {
            const res = await this.fetchFn(`${this.base}/v1/towers/${encodeURIComponent(deviceId)}/snapshot/cam${camera}`, { headers: this.headers({ Accept: 'image/jpeg' }), signal: ac.signal });
            if (!res.ok) {
                let body;
                try {
                    body = await res.json();
                }
                catch {
                    body = null;
                }
                throw errorFromResponse(res.status, body);
            }
            return await res.blob();
        }
        finally {
            clearTimeout(timer);
        }
    }
    async towerStatus(deviceId) {
        return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}/status`);
    }
    async towerStreams(deviceId) {
        return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}/streams`);
    }
    /** Continuous NVR recording status (desired + MediaMTX effective). */
    async getRecording(deviceId) {
        return this.request('GET', `/v1/towers/${encodeURIComponent(deviceId)}/recording`);
    }
    /** Enable/disable continuous recording on all cameras for this tower. */
    async setRecording(deviceId, enabled) {
        return this.request('PUT', `/v1/towers/${encodeURIComponent(deviceId)}/recording`, {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled }),
            timeout: 60_000,
        });
    }
    // ── alerts ───────────────────────────────────────────────────────────────
    async listAlerts(opts = {}) {
        const p = new URLSearchParams();
        if (opts.customerId)
            p.set('customer_id', opts.customerId);
        if (opts.deviceId)
            p.set('device_id', opts.deviceId);
        if (opts.limit != null)
            p.set('limit', String(opts.limit));
        const q = p.toString();
        const data = await this.request('GET', `/v1/alerts${q ? `?${q}` : ''}`);
        return data.alerts ?? [];
    }
    async listCustomerAlerts(customerId, limit = 100) {
        const data = await this.request('GET', `/v1/customers/${encodeURIComponent(customerId)}/alerts?limit=${limit}`);
        return data.alerts ?? [];
    }
    /** SSE URL for live alerts (use fetch-event-source or same-origin proxy for auth headers). */
    eventsUrl(customerId) {
        const p = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : '';
        return `${this.base}/v1/events${p}`;
    }
}
