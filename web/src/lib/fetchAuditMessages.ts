import { API_URL } from "../config";
import {
  messagesFromAuditEntries,
  type StoredChatMessage,
} from "./chatPersistence";
import type { AuditLogsResponse } from "../types/audit";

export async function fetchAuditMessagesForThread(
  threadId: string,
  options?: { source?: string },
): Promise<StoredChatMessage[]> {
  const res = await fetch(
    `${API_URL}/api/audit/logs?thread_id=${encodeURIComponent(threadId)}&limit=200`,
  );
  if (!res.ok) return [];
  const data = (await res.json()) as AuditLogsResponse;
  let entries = data.entries ?? [];
  if (options?.source) {
    entries = entries.filter((entry) => entry.source === options.source);
  }
  if (!entries.length) return [];
  return messagesFromAuditEntries(entries);
}
