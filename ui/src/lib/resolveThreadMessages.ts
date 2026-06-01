import { fetchAuditMessagesForThread } from "./fetchAuditMessages";
import {
  loadThreadMessages,
  mergeLocalAndAuditTranscripts,
  type StoredChatMessage,
} from "./chatPersistence";
import { fetchMessagesFromApi } from "./sessionApi";

/** Load chat transcript: Postgres API → localStorage → audit fallback. */
export async function resolveThreadMessages(
  threadId: string,
): Promise<StoredChatMessage[]> {
  const fromApi = await fetchMessagesFromApi(threadId);
  if (fromApi != null && fromApi.length > 0) {
    return fromApi;
  }

  const local = loadThreadMessages(threadId);
  let audit: StoredChatMessage[] = [];
  try {
    audit = await fetchAuditMessagesForThread(threadId);
  } catch {
    audit = [];
  }
  if (fromApi != null && fromApi.length === 0 && local.length === 0 && audit.length === 0) {
    return [];
  }
  if (local.length === 0) return audit;
  if (audit.length === 0) return local;
  return mergeLocalAndAuditTranscripts(local, audit);
}
