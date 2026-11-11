import { useEffect, useRef, useState, useCallback, type DependencyList } from "react";

interface UseAsyncState<T> {
  data: T | undefined;
  loading: boolean;
  error: Error | null;
  /** refetch(true): tải ngầm (realtime), giữ dữ liệu cũ trên màn hình, không bật loading. */
  refetch: (ngam?: unknown) => void;
}

/**
 * Wraps any async fetcher (from src/api/*.ts) with loading/error/data state.
 * Used by every page instead of each page hand-rolling its own useEffect.
 */
export function useAsync<T>(fetcher: () => Promise<T>, deps: DependencyList = []): UseAsyncState<T> {
  const [data, setData] = useState<T>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const ngamRef = useRef(false);

  const run = useCallback(() => {
    let cancelled = false;
    if (!ngamRef.current) setLoading(true);
    ngamRef.current = false;
    setError(null);
    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err : new Error(String(err)));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadKey]);

  useEffect(() => run(), [run]);

  const refetch = useCallback((ngam?: unknown) => {
    ngamRef.current = ngam === true; // nút bấm truyền event → vẫn hiện loading
    setReloadKey((k) => k + 1);
  }, []);

  return { data, loading, error, refetch };
}
