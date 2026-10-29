import { useEffect, useState, useCallback, type DependencyList } from "react";

interface UseAsyncState<T> {
  data: T | undefined;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
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

  const run = useCallback(() => {
    let cancelled = false;
    setLoading(true);
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

  return { data, loading, error, refetch: () => setReloadKey((k) => k + 1) };
}
