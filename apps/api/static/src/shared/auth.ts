import { createSignal } from "solid-js";

const storageKey = "sync.jwt";

function readTokenFromStorage(): string | null {
  const value = window.localStorage.getItem(storageKey);
  if (value === null) {
    return null;
  }
  if (value.trim() === "") {
    throw new Error("Некорректный JWT в localStorage.");
  }
  return value;
}

const [token, setTokenSignal] = createSignal<string | null>(readTokenFromStorage());

export function getAuthToken(): string | null {
  return token();
}

export function setAuthToken(next: string | null): void {
  setTokenSignal(next);
  if (next === null) {
    window.localStorage.removeItem(storageKey);
    return;
  }
  if (next.trim() === "") {
    throw new Error("JWT не должен быть пустым.");
  }
  window.localStorage.setItem(storageKey, next);
}

export function getCurrentUserId(): string | null {
  const jwt = getAuthToken();
  if (jwt === null) {
    return null;
  }
  const parts = jwt.split(".");
  if (parts.length !== 3) {
    throw new Error("Некорректный JWT: ожидались 3 части.");
  }
  const payloadJson = decodeBase64Url(parts[1]);
  const payload = JSON.parse(payloadJson) as unknown;
  if (!payload || typeof payload !== "object") {
    throw new Error("Некорректный JWT payload.");
  }
  const sub = (payload as Record<string, unknown>)["sub"];
  if (typeof sub !== "string" || sub.trim() === "") {
    throw new Error("Некорректный JWT: payload.sub обязателен.");
  }
  return sub;
}

function decodeBase64Url(input: string): string {
  if (input.trim() === "") {
    throw new Error("Некорректный base64url: пустая строка.");
  }
  const padded = input + "=".repeat((4 - (input.length % 4)) % 4);
  const b64 = padded.replace(/-/g, "+").replace(/_/g, "/");
  return atob(b64);
}

