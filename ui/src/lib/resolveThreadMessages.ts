import { fetchAuditMessagesForThread } from "./fetchAuditMessages";
import { loadThreadMessages, type StoredChatMessage } from "./chatPersistence";

/** Load chat transcript for a thread: browser snapshot first, then audit fallback. */
export async function resolveThreadMessages(
  threadId: string,
): Promise<StoredChatMessage[]> {
  const local = loadThreadMessages(threadId);
  if (local.length > 0) return local;
  try {
    return await fetchAuditMessagesForThread(threadId);
  } catch {
    return [];
  }
}
