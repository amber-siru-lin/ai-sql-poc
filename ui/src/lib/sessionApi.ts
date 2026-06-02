import { API_URL, type SemanticLayerMode } from "../config";
import type { AuditSession } from "../types/audit";
import type { StoredChatMessage } from "./chatPersistence";

const SEMANTIC_LAYER_KEY = "ai-sql-poc-semantic-layer";
const SNAPSHOTS_KEY = "ai-sql-poc-chat-snapshots";
const MIGRATION_KEY = "ai-sql-poc-snapshots-migrated-v1";

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

/** One-time migration: push legacy localStorage snapshots to Postgres, then delete them. */
export async function migrateLocalSnapshotsOnce(): Promise<void> {
  if (!isSessionsApiAvailable()) return;
  if (localStorage.getItem(MIGRATION_KEY)) return;

  const raw = localStorage.getItem(SNAPSHOTS_KEY);
  if (raw) {
    try {
      const store = JSON.parse(raw) as Record<string, StoredChatMessage[]>;
      const entries = Object.entries(store).filter(
        ([, msgs]) => Array.isArray(msgs) && msgs.length > 0,
      );
      await Promise.all(
        entries.map(([threadId, messages]) => saveMessagesToApi(threadId, messages)),
      );
    } catch {
      // Ignore corrupt snapshot blob.
    }
    localStorage.removeItem(SNAPSHOTS_KEY);
  }

  localStorage.setItem(MIGRATION_KEY, "1");
}
