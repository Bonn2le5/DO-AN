import axios from "axios";

/** Central HTTP client for the Django REST API. */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  headers: { "Content-Type": "application/json" },
});

export function setAccessToken(token: string | null) {
  if (token) localStorage.setItem("access_token", token);
  else localStorage.removeItem("access_token");
}

export function setRefreshToken(token: string | null) {
  if (token) localStorage.setItem("refresh_token", token);
  else localStorage.removeItem("refresh_token");
}

export function clearTokens() {
  setAccessToken(null);
  setRefreshToken(null);
}

let refreshInFlight: Promise<string | null> | null = null;

function tokenExpiry(token: string): number {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = payload.padEnd(Math.ceil(payload.length / 4) * 4, "=");
    return JSON.parse(atob(padded)).exp * 1000;
  } catch {
    return 0;
  }
}

export function getAccessTokenExpiry(): number {
  const token = localStorage.getItem("access_token");
  return token ? tokenExpiry(token) : 0;
}

export function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) {
    clearTokens();
    window.dispatchEvent(new Event("auth:expired"));
    return Promise.resolve(null);
  }

  refreshInFlight ??= axios
    .post(`${apiClient.defaults.baseURL}/auth/refresh/`, { refresh: refreshToken })
    .then(({ data }) => {
      const access = data.access as string;
      setAccessToken(access);
      if (data.refresh) setRefreshToken(data.refresh as string);
      window.dispatchEvent(new Event("auth:token-refreshed"));
      return access;
    })
    .catch(() => {
      clearTokens();
      window.dispatchEvent(new Event("auth:expired"));
      return null;
    })
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

/** Refreshes shortly before expiry, so REST calls and WebSocket reconnects share one token. */
export async function ensureFreshToken(): Promise<string | null> {
  const token = localStorage.getItem("access_token");
  if (token && tokenExpiry(token) - Date.now() > 60_000) return token;
  return refreshAccessToken();
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config as
      | (typeof error.config & { _retriedAfterRefresh?: boolean })
      | undefined;
    const requestUrl = String(request?.url ?? "");
    if (
      error.response?.status !== 401 ||
      !request ||
      request._retriedAfterRefresh ||
      requestUrl.includes("/auth/login/") ||
      requestUrl.includes("/auth/refresh/")
    ) {
      return Promise.reject(error);
    }

    request._retriedAfterRefresh = true;
    const nextAccessToken = await refreshAccessToken();
    if (!nextAccessToken) return Promise.reject(error);

    request.headers.set("Authorization", `Bearer ${nextAccessToken}`);
    return apiClient(request);
  },
);
