import { useCallback, useEffect, useState, type DependencyList } from "react";

export function useAsync<T>(loader: () => Promise<T>, deps: DependencyList = []) {
  const [data, setData] = useState<T>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>();

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    try {
      setData(await loader());
    } catch (cause) {
      setError(cause);
      console.error("Không thể tải dữ liệu giao diện quản trị:", cause);
    } finally {
      setLoading(false);
    }
  }, [loader, ...deps]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
