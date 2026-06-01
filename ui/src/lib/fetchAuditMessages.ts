import { API_URL } from "../config";
import {
  messagesFromAuditEntries,
  type StoredChatMessage,
} from "./chatPersistence";
import type { AuditLogsResponse } from "../types/audit";

export async function fetchAuditMessagesForThread(
  threadId: string,
): Promise<StoredChatMessage[]> {
  const res = await fetch(
    `${API_URL}/api/audit/logs?thread_id=${encodeURIComponent(threadId)}&limit=200`,
  );
  if (!res.ok) return [];
  const data = (await res.json()) as AuditLogsResponse;
  if (!data.entries?.length) return [];
  return messagesFromAuditEntries(data.entries);
}
