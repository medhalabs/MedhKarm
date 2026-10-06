/**
 * The single place the frontend talks to the backend API, from the Next.js server only (server
 * components, server actions, route handlers): it adds the signed-in founder's session token.
 * Features call `apiGet` / `apiPost` from their own `api/` folder; components never call fetch directly.
 */

import { sessionToken } from "./session";

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
  const token = await sessionToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      body?.error?.code ?? "unknown_error",
      body?.error?.message ?? validationMessage(body) ?? response.statusText,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** The first validation problem FastAPI reports ({"detail": [{"msg": "Value error, …"}]}), in
 * plain words, or undefined when the body isn't one. */
export function validationMessage(body: unknown): string | undefined {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (!Array.isArray(detail)) return undefined;
  const first = detail[0] as { msg?: unknown; loc?: unknown } | undefined;
  if (typeof first?.msg !== "string") return undefined;
  return first.msg.replace(/^Value error, /, "");
}

/** Full URL of a backend path, for things that can't go through `request` (e.g. streaming). */
export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

export function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "GET" });
}

export function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "POST", body: JSON.stringify(body) });
}

export function apiPatch<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "PATCH", body: JSON.stringify(body) });
}

export function apiPut<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, { ...init, method: "PUT", body: JSON.stringify(body) });
}

export function apiDelete(path: string, init?: RequestInit): Promise<void> {
  return request<void>(path, { ...init, method: "DELETE" });
}
