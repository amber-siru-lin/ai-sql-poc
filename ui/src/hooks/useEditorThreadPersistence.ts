import type { MutableRefObject } from "react";
import { useCallback, useEffect, useRef } from "react";

import { toStoredMessages } from "../lib/chatPersistence";
import { saveEditorThreadMessages } from "../lib/editorChatPersistence";
import { useEditorAgent } from "./useEditorAgent";

const AUTOSAVE_DEBOUNCE_MS = 400;

export function useEditorThreadPersistence(
  threadId: string,
  editorOwnerThreadIdRef: MutableRefObject<string>,
) {
  const { agent } = useEditorAgent({ watchMessages: true });
  const messages = agent?.messages;
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const threadIdRef = useRef(threadId);
  threadIdRef.current = threadId;

  const flush = useCallback(() => {
    const storable = toStoredMessages(messagesRef.current);
    if (storable.length > 0) {
      saveEditorThreadMessages(threadIdRef.current, storable);
    }
  }, []);

  useEffect(() => {
    if (!messages?.length) return;
    if (threadId !== editorOwnerThreadIdRef.current) return;
    if (agent?.isRunning) return;

    const timer = window.setTimeout(() => {
      if (threadId !== editorOwnerThreadIdRef.current) return;
      if (agent?.isRunning) return;
      const storable = toStoredMessages(messages);
      if (storable.length > 0) {
        saveEditorThreadMessages(threadId, storable);
      }
    }, AUTOSAVE_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [messages, threadId, agent?.isRunning, editorOwnerThreadIdRef, agent]);

  useEffect(() => {
    if (agent?.isRunning) return;
    if (!messages?.length) return;
    if (threadId !== editorOwnerThreadIdRef.current) return;
    const storable = toStoredMessages(messages);
    if (storable.length > 0) {
      saveEditorThreadMessages(threadId, storable);
    }
  }, [agent?.isRunning, messages, threadId, editorOwnerThreadIdRef, agent]);

  useEffect(() => {
    return () => {
      const storable = toStoredMessages(messagesRef.current);
      if (storable.length > 0) {
        saveEditorThreadMessages(threadIdRef.current, storable);
      }
    };
  }, []);

  return { flush };
}
