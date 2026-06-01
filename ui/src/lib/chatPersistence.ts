import type { Message } from "@copilotkit/react-core";

import type { AuditLogEntry } from "../types/audit";

const STORAGE_KEY = "ai-sql-poc-chat-snapshots";

type SnapshotStore = Record<string, Message[]>;

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

export function loadThreadMessages(threadId: string): Message[] {
  const store = readStore();
  const messages = store[threadId];
  return Array.isArray(messages) ? messages : [];
}

export function saveThreadMessages(threadId: string, messages: Message[]): void {
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
export function messagesFromAuditEntries(entries: AuditLogEntry[]): Message[] {
  const ordered = [...entries].sort((a, b) =>
    (a.timestamp || "").localeCompare(b.timestamp || ""),
  );
  const messages: Message[] = [];

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
