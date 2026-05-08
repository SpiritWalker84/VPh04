import type { AdminSetting } from "./types";

const API_BASE = "/api/v1";

const withCreds: RequestInit = { credentials: "include" };

async function parseJson<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { ...withCreds });
  if (!response.ok) {
    throw new Error(`GET ${path}: ${response.status} ${await response.text()}`);
  }
  return parseJson<T>(response);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...withCreds,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path}: ${response.status} ${await response.text()}`);
  }
  return parseJson<T>(response);
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...withCreds,
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`PATCH ${path}: ${response.status} ${await response.text()}`);
  }
  return parseJson<T>(response);
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, { ...withCreds, method: "DELETE" });
  if (!response.ok) {
    throw new Error(`DELETE ${path}: ${response.status} ${await response.text()}`);
  }
}

export async function authMe(): Promise<{ authenticated: boolean }> {
  return apiGet<{ authenticated: boolean }>("/auth/me");
}

export async function authLogin(username: string, password: string): Promise<void> {
  await apiPost<{ ok: boolean }>("/auth/login", { username, password });
}

export async function authLogout(): Promise<void> {
  await apiPost<{ ok: boolean }>("/auth/logout", {});
}

export async function fetchAdminSettingsActive(): Promise<AdminSetting[]> {
  return apiGet<AdminSetting[]>("/admin/settings");
}

export async function fetchAdminSettingsAll(): Promise<AdminSetting[]> {
  return apiGet<AdminSetting[]>("/admin/settings/all");
}
