import { API_URL, type SemanticLayerMode } from "../config";
import type { AuditSession } from "../types/audit";
import type { StoredChatMessage } from "./chatPersistence";

const SEMANTIC_LAYER_KEY = "ai-sql-poc-semantic-layer";

export type SessionsStatus = {
  backend: string;
  available: boolean;
};

let sessionsAvailableCache: boolean | null = null;

export function setSessionsAvailableFromStatus(sessions?: SessionsStatus | null): void {
  if (sessions != null) {
    sessionsAvailableCache = sessions.available;
  }
}

export function isSessionsApiAvailable(): boolean {
  return sessionsAvailableCache === true;
}

function currentSemanticLayer(): SemanticLayerMode {
  const stored = localStorage.getItem(SEMANTIC_LAYER_KEY);
  if (stored === "off" || stored === "wren" || stored === "cortex") {
    return stored;
  }
  return "off";
}

export type SessionsListResponse = {
  sessions: AuditSession[];
};

export type SessionMessagesResponse = {
  thread_id: string;
  messages: StoredChatMessage[];
};

export async function fetchSessionsFromApi(limit = 40): Promise<AuditSession[] | null> {
  try {
    const res = await fetch(`${API_URL}/api/sessions?limit=${limit}`);
    if (res.status === 503) return null;
    if (!res.ok) return null;
    const json = (await res.json()) as SessionsListResponse;
    return json.sessions ?? [];
  } catch {
    return null;
  }
}

export async function createSessionOnApi(
  threadId: string,
  options?: { title?: string; semanticLayer?: SemanticLayerMode },
): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: threadId,
        title: options?.title ?? "New chat",
        semantic_layer: options?.semanticLayer ?? currentSemanticLayer(),
      }),
    });
    return res.ok || res.status === 409;
  } catch {
    return false;
  }
}

export async function fetchMessagesFromApi(
  threadId: string,
): Promise<StoredChatMessage[] | null> {
  try {
    const res = await fetch(
      `${API_URL}/api/sessions/${encodeURIComponent(threadId)}/messages`,
    );
    if (res.status === 503) return null;
    if (res.status === 404) return [];
    if (!res.ok) return null;
    const json = (await res.json()) as SessionMessagesResponse;
    return json.messages ?? [];
  } catch {
    return null;
  }
}

export async function saveMessagesToApi(
  threadId: string,
  messages: StoredChatMessage[],
  semanticLayer?: SemanticLayerMode,
): Promise<boolean> {
  if (messages.length === 0) return false;
  try {
    const res = await fetch(
      `${API_URL}/api/sessions/${encodeURIComponent(threadId)}/messages`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages,
          semantic_layer: semanticLayer ?? currentSemanticLayer(),
        }),
      },
    );
    return res.ok;
  } catch {
    return false;
  }
}

/** Push all localStorage snapshots to Postgres when API is available. */
export async function backfillLocalSnapshotsToApi(): Promise<void> {
  if (!isSessionsApiAvailable()) return;
  const raw = localStorage.getItem("ai-sql-poc-chat-snapshots");
  if (!raw) return;
  let store: Record<string, StoredChatMessage[]>;
  try {
    store = JSON.parse(raw) as Record<string, StoredChatMessage[]>;
  } catch {
    return;
  }
  const entries = Object.entries(store).filter(
    ([, msgs]) => Array.isArray(msgs) && msgs.length > 0,
  );
  await Promise.all(
    entries.map(([threadId, messages]) => saveMessagesToApi(threadId, messages)),
  );
}
