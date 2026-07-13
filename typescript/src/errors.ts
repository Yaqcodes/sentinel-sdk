export class SentinelError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly context: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = 'SentinelError';
  }
}

export class AuthError extends SentinelError {}
export class NotFoundError extends SentinelError {}
export class InvalidRequestError extends SentinelError {}
export class TowerNotEnrolledError extends SentinelError {}
export class TowerOfflineError extends SentinelError {}
export class TowerError extends SentinelError {}

const MAP: Record<string, typeof SentinelError> = {
  unauthorized: AuthError,
  not_found: NotFoundError,
  invalid_request: InvalidRequestError,
  tower_not_enrolled: TowerNotEnrolledError,
  tower_offline: TowerOfflineError,
  tower_error: TowerError,
};

export function errorFromResponse(status: number, body: unknown): SentinelError {
  let code = 'unknown_error';
  let message = `HTTP ${status}`;
  let context: Record<string, unknown> = {};

  if (body && typeof body === 'object') {
    const o = body as Record<string, unknown>;
    if (o.error && typeof o.error === 'object') {
      const err = o.error as Record<string, unknown>;
      code = String(err.code ?? code);
      message = String(err.message ?? message);
      context = Object.fromEntries(
        Object.entries(err).filter(([k]) => k !== 'code' && k !== 'message'),
      );
    } else if ('detail' in o) {
      message = String(o.detail);
      code = status === 401 ? 'unauthorized' : status === 404 ? 'not_found' : 'api_error';
    }
  }

  const Cls = MAP[code] ?? SentinelError;
  return new Cls(message, status, code, context);
}
