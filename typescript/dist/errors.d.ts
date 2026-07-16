export declare class SentinelError extends Error {
    readonly status: number;
    readonly code: string;
    readonly context: Record<string, unknown>;
    constructor(message: string, status: number, code: string, context?: Record<string, unknown>);
}
export declare class AuthError extends SentinelError {
}
export declare class NotFoundError extends SentinelError {
}
export declare class InvalidRequestError extends SentinelError {
}
export declare class TowerNotEnrolledError extends SentinelError {
}
export declare class TowerOfflineError extends SentinelError {
}
export declare class TowerError extends SentinelError {
}
export declare function errorFromResponse(status: number, body: unknown): SentinelError;
//# sourceMappingURL=errors.d.ts.map