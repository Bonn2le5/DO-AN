/**
 * Central WebSocket URL resolver and reconnecting client helper.
 * Path: moc-frontend/src/services/websocket.ts
 */
import {
  ensureFreshToken,
  getAccessTokenExpiry,
  refreshAccessToken,
} from "@/api/client";

export function getWebSocketUrl(path: string, accessToken?: string): string {
  // If absolute ws:// or wss:// is provided, return directly
  if (path.startsWith("ws://") || path.startsWith("wss://")) {
    return path;
  }

  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const envWsUrl = import.meta.env.VITE_WS_URL as string | undefined;

  const envApiUrl = import.meta.env.VITE_API_URL as string | undefined;

  let base = "";
  if (envWsUrl) {
    base = `${envWsUrl.replace(/\/+$/, "")}${cleanPath}`;
  } else if (envApiUrl && /^https?:\/\//i.test(envApiUrl)) {
    // Backend ở tên miền riêng (vd. https://api.mockitchen.id.vn/api): WebSocket mở tới cùng máy chủ đó.
    const api = new URL(envApiUrl);
    base = `${api.protocol === "https:" ? "wss:" : "ws:"}//${api.host}${cleanPath}`;
  } else {
    const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
    const protocol = isHttps ? "wss:" : "ws:";
    const isDev =
      typeof window !== "undefined" &&
      (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

    // In dev, Django Channels runs on port 8000
    const host = isDev ? `${window.location.hostname}:8000` : window.location.host;
    base = `${protocol}//${host}${cleanPath}`;
  }

  // Inject JWT token from localStorage
  const token =
    accessToken ??
    (typeof window !== "undefined" ? localStorage.getItem("access_token") : null);
  if (token) {
    const separator = base.includes("?") ? "&" : "?";
    return `${base}${separator}token=${encodeURIComponent(token)}`;
  }

  return base;
}

/** Connect only with a current access token. */
export async function openAuthenticatedWebSocket(path: string): Promise<WebSocket | null> {
  const token = await ensureFreshToken();
  if (!token) return null;
  return new WebSocket(getWebSocketUrl(path, token));
}

/** Refresh before the JWT expires, then close so the caller reconnects with the new token. */
export function scheduleWebSocketRenewal(
  socket: WebSocket,
  expiry: number,
): () => void {
  const timer = window.setTimeout(async () => {
    const token = await refreshAccessToken();
    if (token && socket.readyState < WebSocket.CLOSING) {
      socket.close(4001, "access token renewed");
    }
  }, Math.max(0, expiry - Date.now() - 60_000));
  return () => window.clearTimeout(timer);
}

export function scheduleCurrentWebSocketRenewal(socket: WebSocket): () => void {
  return scheduleWebSocketRenewal(socket, getAccessTokenExpiry());
}
