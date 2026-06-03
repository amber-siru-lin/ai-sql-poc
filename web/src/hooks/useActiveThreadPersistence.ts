import type { MutableRefObject } from "react";
import { useCallback, useEffect, useRef } from "react";

import { saveThreadMessages, toStoredMessages } from "../lib/chatPersistence";
import { useSqlAgent } from "./useSqlAgent";

const AUTOSAVE_DEBOUNCE_MS = 400;

/** Persist the active thread's messages; expose flush() for save-before-switch. */
export function useActiveThreadPersistence(
  threadId: string,
  copilotOwnerThreadIdRef: MutableRefObject<string>,
) {
  const { agent } = useSqlAgent({ watchMessages: true });
  const messages = agent?.messages;
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const threadIdRef = useRef(threadId);
  threadIdRef.current = threadId;

  const flush = useCallback(() => {
    const storable = toStoredMessages(messagesRef.current);
    if (storable.length > 0) {
      saveThreadMessages(threadIdRef.current, storable);
    }
  }, []);

  useEffect(() => {
    if (!messages?.length) return;
    if (threadId !== copilotOwnerThreadIdRef.current) return;
    if (agent?.isRunning) return;

    const timer = window.setTimeout(() => {
      if (threadId !== copilotOwnerThreadIdRef.current) return;
      if (agent?.isRunning) return;
      const storable = toStoredMessages(messages);
      if (storable.length > 0) {
        saveThreadMessages(threadId, storable);
      }
    }, AUTOSAVE_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [messages, threadId, agent?.isRunning, copilotOwnerThreadIdRef, agent]);

  useEffect(() => {
    if (agent?.isRunning) return;
    if (!messages?.length) return;
    if (threadId !== copilotOwnerThreadIdRef.current) return;
    const storable = toStoredMessages(messages);
    if (storable.length > 0) {
      saveThreadMessages(threadId, storable);
    }
  }, [agent?.isRunning, messages, threadId, copilotOwnerThreadIdRef, agent]);

  return { flush };
}
