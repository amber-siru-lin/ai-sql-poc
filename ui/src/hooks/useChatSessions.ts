import { useCallback, useEffect, useState } from "react";

import { API_URL } from "../config";
import { fetchSessionsFromApi } from "../lib/sessionApi";
import type { AuditSession, AuditSessionsResponse } from "../types/audit";

async function fetchAuditSessions(limit: number): Promise<AuditSession[]> {
  const res = await fetch(`${API_URL}/api/audit/sessions?limit=${limit}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = (await res.json()) as AuditSessionsResponse;
  return json.sessions ?? [];
}

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
      setSessions(await fetchAuditSessions(40));
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
