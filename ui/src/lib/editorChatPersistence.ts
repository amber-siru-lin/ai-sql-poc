import type { StoredChatMessage } from "./chatPersistence";

const EDITOR_SNAPSHOTS_KEY = "ai-sql-poc-editor-chat-snapshots";

type SnapshotStore = Record<string, StoredChatMessage[]>;

function readStore(): SnapshotStore {
  try {
    const raw = localStorage.getItem(EDITOR_SNAPSHOTS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as SnapshotStore;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeStore(store: SnapshotStore): void {
  try {
    localStorage.setItem(EDITOR_SNAPSHOTS_KEY, JSON.stringify(store));
  } catch {
    // ignore quota errors
  }
}

export function loadEditorThreadMessages(threadId: string): StoredChatMessage[] {
  const store = readStore();
  const messages = store[threadId];
  return Array.isArray(messages) ? messages : [];
}

export function saveEditorThreadMessages(threadId: string, messages: StoredChatMessage[]): void {
  if (messages.length === 0) return;
  const store = readStore();
  store[threadId] = messages.slice(-80);
  writeStore(store);
}
