/**
 * Central WebSocket URL resolver and reconnecting client helper.
 * Path: moc-frontend/src/services/websocket.ts
 */

export function getWebSocketUrl(path: string): string {
  // If absolute ws:// or wss:// is provided, return directly
  if (path.startsWith("ws://") || path.startsWith("wss://")) {
    return path;
  }

  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const envWsUrl = import.meta.env.VITE_WS_URL as string | undefined;

  let base = "";
  if (envWsUrl) {
    base = `${envWsUrl.replace(/\/+$/, "")}${cleanPath}`;
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
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    const separator = base.includes("?") ? "&" : "?";
    return `${base}${separator}token=${encodeURIComponent(token)}`;
  }

  return base;
}
