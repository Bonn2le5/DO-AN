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

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config as (typeof error.config & { _retriedAfterRefresh?: boolean }) | undefined;
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
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      clearTokens();
      return Promise.reject(error);
    }

    refreshInFlight ??= axios
      .post(`${apiClient.defaults.baseURL}/auth/refresh/`, { refresh: refreshToken })
      .then(({ data }) => {
        const nextAccessToken = data.access as string;
        setAccessToken(nextAccessToken);
        if (data.refresh) setRefreshToken(data.refresh as string);
        return nextAccessToken;
      })
      .catch(() => {
        clearTokens();
        return null;
      })
      .finally(() => {
        refreshInFlight = null;
      });

    const nextAccessToken = await refreshInFlight;
    if (!nextAccessToken) return Promise.reject(error);

    request.headers.set("Authorization", `Bearer ${nextAccessToken}`);
    return apiClient(request);
  }
);
