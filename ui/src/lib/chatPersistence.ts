import type { AuditLogEntry } from "../types/audit";

/** Minimal shape CopilotKit accepts via setMessages. */
export type StoredChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

const STORAGE_KEY = "ai-sql-poc-chat-snapshots";

type SnapshotStore = Record<string, StoredChatMessage[]>;

function readStore(): SnapshotStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as SnapshotStore;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeStore(store: SnapshotStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // Quota exceeded or private mode — ignore.
  }
}

export function loadThreadMessages(threadId: string): StoredChatMessage[] {
  const store = readStore();
  const messages = store[threadId];
  return Array.isArray(messages) ? messages : [];
}

/** Serialize CopilotKit messages for localStorage. */
export function toStoredMessages(messages: unknown): StoredChatMessage[] {
  if (!Array.isArray(messages)) return [];
  const stored: StoredChatMessage[] = [];
  for (const m of messages) {
    if (!m || typeof m !== "object") continue;
    const msg = m as { id?: string; role?: string; content?: unknown };
    if (msg.role !== "user" && msg.role !== "assistant" && msg.role !== "system") {
      continue;
    }
    if (!msg.id) continue;
    let content = "";
    if (typeof msg.content === "string") {
      content = msg.content;
    } else if (Array.isArray(msg.content)) {
      content = msg.content
        .map((block) => {
          if (typeof block === "string") return block;
          if (block && typeof block === "object") {
            if ("text" in block) return String((block as { text?: string }).text ?? "");
            if ("type" in block && (block as { type?: string }).type === "text") {
              return String((block as { text?: string }).text ?? "");
            }
          }
          return "";
        })
        .filter(Boolean)
        .join("\n");
    } else if (msg.content != null) {
      content = JSON.stringify(msg.content);
    }
    if (!content.trim() && msg.role !== "user") continue;
    if (!content.trim()) content = "(empty message)";
    stored.push({
      id: msg.id,
      role: msg.role as StoredChatMessage["role"],
      content,
    });
  }
  return stored;
}

export function saveThreadMessages(threadId: string, messages: StoredChatMessage[]): void {
  if (messages.length === 0) return;
  const store = readStore();
  store[threadId] = messages.slice(-80);
  writeStore(store);
}

export function clearThreadMessages(threadId: string): void {
  const store = readStore();
  delete store[threadId];
  writeStore(store);
}

function assistantContentFromAudit(entry: AuditLogEntry): string {
  const parts: string[] = [];
  if (entry.error) {
    parts.push(`**Error:** ${entry.error}`);
  }
  for (const step of entry.sql_executions ?? []) {
    if (step.sql) {
      parts.push(`\`\`\`sql\n${step.sql}\n\`\`\``);
    }
    if (step.error) {
      parts.push(`**SQL error:** ${step.error}`);
    } else if (step.result_preview) {
      parts.push(step.result_preview);
    }
  }
  if (parts.length === 0) {
    return entry.status === "error" ? "Run failed." : "Completed.";
  }
  return parts.join("\n\n");
}

/** Rebuild a read-only chat transcript from audit runs (oldest first). */
export function messagesFromAuditEntries(entries: AuditLogEntry[]): StoredChatMessage[] {
  const ordered = [...entries].sort((a, b) =>
    (a.timestamp || "").localeCompare(b.timestamp || ""),
  );
  const messages: StoredChatMessage[] = [];

  for (const entry of ordered) {
    if (entry.question) {
      messages.push({
        id: `${entry.run_id}-user`,
        role: "user",
        content: entry.question,
      });
    }
    messages.push({
      id: `${entry.run_id}-assistant`,
      role: "assistant",
      content: assistantContentFromAudit(entry),
    });
  }

  return messages;
}
