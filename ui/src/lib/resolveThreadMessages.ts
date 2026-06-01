import { fetchAuditMessagesForThread } from "./fetchAuditMessages";
import { loadThreadMessages, type StoredChatMessage } from "./chatPersistence";

/** Load chat transcript for a thread: merge browser snapshot with audit fallback. */
export async function resolveThreadMessages(
  threadId: string,
): Promise<StoredChatMessage[]> {
  const local = loadThreadMessages(threadId);
  let audit: StoredChatMessage[] = [];
  try {
    audit = await fetchAuditMessagesForThread(threadId);
  } catch {
    audit = [];
  }
  if (local.length === 0) return audit;
  if (audit.length === 0) return local;
  return local.length >= audit.length ? local : audit;
}
