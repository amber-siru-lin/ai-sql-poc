import { useCallback, useState } from "react";
import { useCopilotChatHeadless_c } from "@copilotkit/react-core";

export const SESSION_STORAGE_KEY = "ai-sql-poc-thread-id";

export function loadStoredThreadId(): string {
  const stored = localStorage.getItem(SESSION_STORAGE_KEY);
  if (stored && stored.length > 0) return stored;
  return crypto.randomUUID();
}

/** LangGraph thread + CopilotKit chat lifecycle (clear / new conversation). */
export function useChatSession(
  threadId: string,
  onThreadIdChange: (nextId: string) => void,
) {
  const { reset, messages, isLoading } = useCopilotChatHeadless_c();
  const [lastClearedAt, setLastClearedAt] = useState<number | null>(null);

  const startNewConversation = useCallback(() => {
    const nextId = crypto.randomUUID();
    reset();
    onThreadIdChange(nextId);
    localStorage.setItem(SESSION_STORAGE_KEY, nextId);
    setLastClearedAt(Date.now());
  }, [reset, onThreadIdChange]);

  return {
    threadId,
    messages,
    isLoading,
    lastClearedAt,
    startNewConversation,
    messageCount: messages.length,
  };
}
