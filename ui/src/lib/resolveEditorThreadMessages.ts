import { fetchAuditMessagesForThread } from "./fetchAuditMessages";
import { loadEditorThreadMessages } from "./editorChatPersistence";
import {
  mergeLocalAndAuditTranscripts,
  type StoredChatMessage,
} from "./chatPersistence";

/** Load editor chat transcript: local snapshot with audit fallback. */
export async function resolveEditorThreadMessages(
  threadId: string,
): Promise<StoredChatMessage[]> {
  const local = loadEditorThreadMessages(threadId);
  let audit: StoredChatMessage[] = [];
  try {
    audit = await fetchAuditMessagesForThread(threadId, { source: "semantic_editor" });
  } catch {
    audit = [];
  }
  if (local.length === 0) return audit;
  if (audit.length === 0) return local;
  return mergeLocalAndAuditTranscripts(local, audit);
}
