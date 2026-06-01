import { useCopilotChatHeadless_c } from "@copilotkit/react-core";
import { useEffect, useRef } from "react";

import { API_URL } from "../config";
import {
  loadThreadMessages,
  messagesFromAuditEntries,
  saveThreadMessages,
} from "../lib/chatPersistence";
import type { AuditLogsResponse } from "../types/audit";

type Props = {
  threadId: string;
  onSessionsChanged?: () => void;
};

/** Persist chat messages locally and restore when switching threads. */
export function ChatSessionRestore({ threadId, onSessionsChanged }: Props) {
  const { messages, setMessages, isLoading } = useCopilotChatHeadless_c();
  const restoredFor = useRef<string | null>(null);
  const prevCount = useRef(0);

  useEffect(() => {
    if (restoredFor.current === threadId) return;
    restoredFor.current = threadId;

    const local = loadThreadMessages(threadId);
    if (local.length > 0) {
      setMessages(local);
      return;
    }

    void fetch(`${API_URL}/api/audit/logs?thread_id=${encodeURIComponent(threadId)}&limit=200`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: AuditLogsResponse | null) => {
        if (!data?.entries?.length) return;
        const reconstructed = messagesFromAuditEntries(data.entries);
        if (reconstructed.length > 0) {
          setMessages(reconstructed);
        }
      })
      .catch(() => {
        /* ignore — empty chat is fine */
      });
  }, [threadId, setMessages]);

  useEffect(() => {
    if (isLoading) return;
    if (messages.length === 0) return;
    saveThreadMessages(threadId, messages);
    if (messages.length > prevCount.current) {
      onSessionsChanged?.();
    }
    prevCount.current = messages.length;
  }, [messages, threadId, isLoading, onSessionsChanged]);

  return null;
}
