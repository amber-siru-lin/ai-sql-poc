import { useCallback, useEffect, useState } from "react";

import { fetchSessionsFromApi, isSessionsApiAvailable } from "../lib/sessionApi";
import type { AuditSession } from "../types/audit";

const SESSIONS_UNAVAILABLE =
  "Chat history requires Postgres — run docker compose up -d and set DATABASE_URL, then restart the API.";

export function useChatSessions() {
  const [sessions, setSessions] = useState<AuditSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fromApi = await fetchSessionsFromApi(40);
      if (fromApi != null) {
        setSessions(fromApi);
        return;
      }
      setSessions([]);
      if (!isSessionsApiAvailable()) {
        setError(SESSIONS_UNAVAILABLE);
      } else {
        setError("Failed to load sessions from Postgres");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sessions");
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { sessions, loading, error, refresh };
}
