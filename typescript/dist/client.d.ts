import type { Customer, PlatformAlert, PtzMoveBody, PtzStatusResult, PtzStopBody, RecordingStatus, StatusResponse, StreamsResponse, Tower } from './models.js';
export interface SentinelClientOptions {
    apiKey?: string;
    /** Default per-request timeout in ms */
    timeout?: number;
    /** Custom fetch (tests, SSR) */
    fetch?: typeof fetch;
}
export declare class SentinelClient {
    private readonly base;
    private readonly apiKey?;
    private readonly timeout;
    private readonly fetchFn;
    constructor(baseUrl: string, options?: SentinelClientOptions);
    private headers;
    private request;
    listCustomers(): Promise<Customer[]>;
    getCustomer(customerId: string): Promise<Customer>;
    listCustomerTowers(customerId: string): Promise<Tower[]>;
    listTowers(status?: string): Promise<Tower[]>;
    getTower(deviceId: string): Promise<Tower>;
    ptzMove(deviceId: string, body: PtzMoveBody): Promise<Record<string, unknown>>;
    ptzStop(deviceId: string, body?: PtzStopBody): Promise<Record<string, unknown>>;
    ptzStatus(deviceId: string, camera?: number): Promise<PtzStatusResult>;
    snapshot(deviceId: string, camera?: number): Promise<Blob>;
    towerStatus(deviceId: string): Promise<StatusResponse>;
    towerStreams(deviceId: string): Promise<StreamsResponse>;
    /** Continuous NVR recording status (desired + MediaMTX effective). */
    getRecording(deviceId: string): Promise<RecordingStatus>;
    /** Enable/disable continuous recording on all cameras for this tower. */
    setRecording(deviceId: string, enabled: boolean): Promise<RecordingStatus>;
    listAlerts(opts?: {
        customerId?: string;
        deviceId?: string;
        limit?: number;
    }): Promise<PlatformAlert[]>;
    listCustomerAlerts(customerId: string, limit?: number): Promise<PlatformAlert[]>;
    /** SSE URL for live alerts (use fetch-event-source or same-origin proxy for auth headers). */
    eventsUrl(customerId?: string): string;
}
//# sourceMappingURL=client.d.ts.map