import { useCopilotChatHeadless_c } from "@copilotkit/react-core";
import { useCallback, useEffect, useRef } from "react";

import { saveThreadMessages, toStoredMessages } from "../lib/chatPersistence";

/** Persist the active thread's messages; expose flush() for save-before-switch. */
export function useActiveThreadPersistence(threadId: string) {
  const { messages } = useCopilotChatHeadless_c();
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
    const storable = toStoredMessages(messages);
    if (storable.length > 0) {
      saveThreadMessages(threadId, storable);
    }
  }, [messages, threadId]);

  return { flush };
}
