import type { StoredChatMessage } from "./chatPersistence";
import { fetchMessagesFromApi } from "./sessionApi";

/** Load SQL chat transcript from Postgres only (Phase 3.6.3 / 3.6.6). */
export async function resolveThreadMessages(
  threadId: string,
): Promise<StoredChatMessage[]> {
  const fromApi = await fetchMessagesFromApi(threadId);
  if (fromApi == null) {
    return [];
  }
  return fromApi;
}
