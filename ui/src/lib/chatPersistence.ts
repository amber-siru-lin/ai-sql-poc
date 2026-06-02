import type { AuditLogEntry } from "../types/audit";
import { saveMessagesToApi } from "./sessionApi";

/** Minimal shape CopilotKit accepts via setMessages. */
export type StoredChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

/** Serialize CopilotKit messages for Postgres PUT flush. */
export function toStoredMessages(messages: unknown): StoredChatMessage[] {
  if (!Array.isArray(messages)) return [];
  const stored: StoredChatMessage[] = [];
  for (const m of messages) {
    if (!m || typeof m !== "object") continue;
    const msg = m as {
      id?: string;
      role?: string;
      type?: string;
      content?: unknown;
      text?: string;
    };
    const role =
      msg.role ??
      (msg.type === "human" || msg.type === "HumanMessage"
        ? "user"
        : msg.type === "ai" || msg.type === "AIMessage"
          ? "assistant"
          : msg.type);
    if (role !== "user" && role !== "assistant" && role !== "system") {
      continue;
    }
    if (!msg.id) continue;
    let content = "";
    if (typeof msg.text === "string" && msg.text.trim()) {
      content = msg.text;
    } else if (typeof msg.content === "string") {
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
    // Keep user messages even if assistant/tool payloads are empty.
    if (!content.trim() && role !== "user") continue;
    if (!content.trim()) content = "(empty message)";
    stored.push({
      id: msg.id,
      role: role as StoredChatMessage["role"],
      content,
    });
  }
  return stored;
}

export function transcriptsMatch(
  current: unknown,
  loaded: StoredChatMessage[],
): boolean {
  const stored = toStoredMessages(current);
  if (stored.length !== loaded.length) return false;
  for (let i = 0; i < stored.length; i++) {
    if (stored[i].id !== loaded[i].id || stored[i].content !== loaded[i].content) {
      return false;
    }
  }
  return true;
}

export function applyThreadTranscript(
  agent: { setMessages: (messages: StoredChatMessage[]) => void },
  loaded: StoredChatMessage[],
  threadId: string,
  ownerThreadIdRef: { current: string },
): void {
  agent.setMessages(loaded);
  ownerThreadIdRef.current = threadId;
}

export function saveThreadMessages(threadId: string, messages: StoredChatMessage[]): void {
  if (messages.length === 0) return;
  void saveMessagesToApi(threadId, messages.slice(-80));
}

export function clearThreadMessages(_threadId: string): void {
  // Chat authority is Postgres only (Phase 3.6.6).
}

function assistantContentFromAudit(entry: AuditLogEntry): string {
  if (entry.assistant_reply?.trim()) {
    return entry.assistant_reply.trim();
  }
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
    const assistantContent = assistantContentFromAudit(entry);
    if (!isAuditPlaceholderAssistant(assistantContent)) {
      messages.push({
        id: `${entry.run_id}-assistant`,
        role: "assistant",
        content: assistantContent,
      });
    }
  }

  return messages;
}

/** Audit fallback text when no SQL steps or assistant prose was stored. */
export function isAuditPlaceholderAssistant(content: string): boolean {
  const trimmed = content.trim();
  return trimmed === "Completed." || trimmed === "Run failed.";
}

/** Prefer the transcript with richer assistant prose (not audit placeholders). */
export function mergeLocalAndAuditTranscripts(
  local: StoredChatMessage[],
  audit: StoredChatMessage[],
): StoredChatMessage[] {
  if (local.length === 0) return audit;
  if (audit.length === 0) return local;

  const assistantQuality = (messages: StoredChatMessage[]) =>
    messages.reduce((score, message) => {
      if (message.role !== "assistant") return score;
      if (isAuditPlaceholderAssistant(message.content)) return score;
      return score + message.content.length;
    }, 0);

  const localQuality = assistantQuality(local);
  const auditQuality = assistantQuality(audit);
  if (localQuality !== auditQuality) {
    return localQuality > auditQuality ? local : audit;
  }
  if (localQuality === 0) {
    return local;
  }
  return local.length >= audit.length ? local : audit;
}
