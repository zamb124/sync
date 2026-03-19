import { getAuthToken } from "./auth";

export type ApiErrorPayload = { detail?: string } | unknown;

export class ApiError extends Error {
  public readonly status: number;
  public readonly payload: ApiErrorPayload;

  public constructor(status: number, payload: ApiErrorPayload) {
    super(`API error: ${status}`);
    this.status = status;
    this.payload = payload;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!path.startsWith("/")) {
    throw new Error("apiFetch ожидает абсолютный path, например /api/spaces.");
  }

  const token = getAuthToken();
  const headers = new Headers(init?.headers);
  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!headers.has("Content-Type") && typeof init?.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(path, {
    ...init,
    headers,
  });

  const contentType = res.headers.get("content-type");
  const isJson = contentType !== null && contentType.includes("application/json");
  const payload = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    throw new ApiError(res.status, payload);
  }

  return payload as T;
}

