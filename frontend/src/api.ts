import type {
  AdminSetting,
  ApplicationDashboardResponse,
  LeadApplicationAdminDetail,
  LeadApplicationAdminListItem,
} from "./types";

const API_BASE = "/api/v1";
const TOKEN_STORAGE_KEY = "vph04_admin_jwt";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export async function apiGet<T>(path: string, opts: { auth?: boolean } = {}): Promise<T> {
  const headers: HeadersInit = {};
  if (opts.auth) Object.assign(headers, authHeaders());
  const response = await fetch(`${API_BASE}${path}`, { headers });
  if (!response.ok) {
    throw new Error(`GET ${path}: ${response.status} ${await response.text()}`);
  }
  return parseJson<T>(response);
}

/** POST без JWT (заявки, логин, регистрация) или с JWT при opts.auth. */
export async function apiPost<T>(path: string, body: unknown, opts: { auth?: boolean } = {}): Promise<T> {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (opts.auth) Object.assign(headers, authHeaders());
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path}: ${response.status} ${await response.text()}`);
  }
  return parseJson<T>(response);
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`PATCH ${path}: ${response.status} ${await response.text()}`);
  }
  return parseJson<T>(response);
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(`DELETE ${path}: ${response.status} ${await response.text()}`);
  }
}

export async function authCheckRegistration(): Promise<{ registration_open: boolean }> {
  return apiGet<{ registration_open: boolean }>("/auth/check");
}

export async function authRegister(username: string, password: string): Promise<void> {
  const data = await apiPost<{ access_token: string }>("/auth/register", { username, password });
  setAccessToken(data.access_token);
}

export async function authLogin(username: string, password: string): Promise<void> {
  const data = await apiPost<{ access_token: string }>("/auth/login", { username, password });
  setAccessToken(data.access_token);
}

export async function authLogout(): Promise<void> {
  clearAccessToken();
  try {
    await apiPost<unknown>("/auth/logout", {});
  } catch {
    /* ignore */
  }
}

export async function authMe(): Promise<{ id: number; username: string } | null> {
  const token = getAccessToken();
  if (!token) return null;
  const response = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
  if (response.status === 401) {
    clearAccessToken();
    return null;
  }
  if (!response.ok) {
    throw new Error(`GET /auth/me: ${response.status} ${await response.text()}`);
  }
  return parseJson<{ id: number; username: string }>(response);
}

export async function fetchAdminSettingsActive(): Promise<AdminSetting[]> {
  return apiGet<AdminSetting[]>("/admin/settings");
}

export async function fetchAdminSettingsAll(): Promise<AdminSetting[]> {
  return apiGet<AdminSetting[]>("/admin/settings/all", { auth: true });
}

/** Публичная отправка анонимных метрик (раз в секунду с лендинга). */
export async function postBehaviorMetrics(payload: {
  application_id?: number;
  time_on_page: number;
  buttons_clicked: string;
  cursor_positions: string;
  return_frequency: number;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/behavior-metrics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      application_id: payload.application_id ?? 0,
      time_on_page: payload.time_on_page,
      buttons_clicked: payload.buttons_clicked,
      cursor_positions: payload.cursor_positions,
      return_frequency: payload.return_frequency,
    }),
  });
  if (!response.ok) {
    console.warn("behavior-metrics POST", response.status, await response.text());
  }
}

export type BehaviorStatsResponse = {
  avg_daily_max_seconds_day: number;
  avg_daily_max_seconds_week: number;
  avg_daily_max_seconds_month: number;
  stream_rows_last_30_days: number;
  heatmap: { x: number; y: number; count: number }[];
  heatmap_grid_px: number;
};

export async function fetchBehaviorStats(): Promise<BehaviorStatsResponse> {
  return apiGet<BehaviorStatsResponse>("/behavior-metrics/stats", { auth: true });
}

export async function fetchApplicationsAdmin(
  skip = 0,
  limit = 100,
  sort: "priority" | "recent" = "priority",
): Promise<LeadApplicationAdminListItem[]> {
  const q = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
    sort,
  });
  return apiGet<LeadApplicationAdminListItem[]>(`/applications?${q}`, { auth: true });
}

export async function fetchApplicationAdmin(id: number): Promise<LeadApplicationAdminDetail> {
  return apiGet<LeadApplicationAdminDetail>(`/applications/${id}`, { auth: true });
}

export async function fetchApplicationsDashboard(): Promise<ApplicationDashboardResponse> {
  return apiGet<ApplicationDashboardResponse>("/applications/dashboard", { auth: true });
}
