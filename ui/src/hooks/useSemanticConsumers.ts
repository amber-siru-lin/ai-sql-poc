import { useCallback, useEffect, useState } from "react";

import { API_URL } from "../config";
import type { SemanticConsumersResponse } from "../types/semanticEditor";

export function useSemanticConsumers() {
  const [data, setData] = useState<SemanticConsumersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/semantic/consumers`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData((await res.json()) as SemanticConsumersResponse);
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : "Failed to load consumers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
