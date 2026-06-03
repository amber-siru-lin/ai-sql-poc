import type { ApiStatusResponse } from '../config';

/** Lambda Function URL + RESPONSE_STREAM may return API Gateway-shaped JSON. */
export function parseApiStatusPayload(raw: unknown): ApiStatusResponse {
  if (raw && typeof raw === 'object' && 'body' in raw) {
    const wrapped = raw as { statusCode?: number; body?: string };
    if (typeof wrapped.body === 'string') {
      return JSON.parse(wrapped.body) as ApiStatusResponse;
    }
  }
  return raw as ApiStatusResponse;
}

export async function fetchApiStatus(apiUrl: string): Promise<ApiStatusResponse> {
  const res = await fetch(`${apiUrl.replace(/\/$/, '')}/api/status`);
  if (!res.ok) throw new Error(`status ${res.status}`);
  return parseApiStatusPayload(await res.json());
}
