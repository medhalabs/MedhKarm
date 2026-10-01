/**
 * The single place the frontend talks to the backend API.
 * Features call `apiGet` / `apiPost` from their own `api/` folder; components never call fetch directly.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      body?.error?.code ?? "unknown_error",
      body?.error?.message ?? response.statusText,
    );
  }

  return (await response.json()) as T;
}

/** Full URL of a backend path, for things that can't go through `request` (e.g. EventSource). */
export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

export function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "GET" });
}

export function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "POST", body: JSON.stringify(body) });
}
