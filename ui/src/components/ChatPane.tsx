import { useCopilotChatHeadless_c } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { AssistantMessage } from "./AssistantMessage";
import { chatMarkdownTagRenderers } from "./chatMarkdownRenderers";
import { resolveThreadMessages } from "../lib/resolveThreadMessages";
import type { StoredChatMessage } from "../lib/chatPersistence";
import "./ChatPane.css";

const CHAT_LABELS = {
  title: "SQL Assistant",
  initial: "Ask a question about TPCH_SF1…",
} as const;

type Props = {
  threadId: string;
  /** Bump to reload the same thread from storage/audit (re-click in sidebar). */
  reloadNonce: number;
  chatInstructions: string;
  onSessionsChanged?: () => void;
};

export function ChatPane({
  threadId,
  reloadNonce,
  chatInstructions,
  onSessionsChanged,
}: Props) {
  const { reset, setMessages, messages, isLoading } = useCopilotChatHeadless_c();
  const [loaded, setLoaded] = useState<StoredChatMessage[] | null>(null);
  const onSessionsChangedRef = useRef(onSessionsChanged);
  onSessionsChangedRef.current = onSessionsChanged;
  const prevCountRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    setLoaded(null);

    void (async () => {
      const resolved = await resolveThreadMessages(threadId);
      if (!cancelled) setLoaded(resolved);
    })();

    return () => {
      cancelled = true;
    };
  }, [threadId, reloadNonce]);

  useLayoutEffect(() => {
    if (loaded === null) return;
    reset();
    setMessages(loaded);
    prevCountRef.current = loaded.length;
  }, [threadId, reloadNonce, loaded, reset, setMessages]);

  useEffect(() => {
    if (loaded === null || isLoading || !messages?.length) return;
    if (messages.length > prevCountRef.current) {
      onSessionsChangedRef.current?.();
    }
    prevCountRef.current = messages.length;
  }, [messages, loaded, isLoading]);

  if (loaded === null) {
    return (
      <div className="chat-pane chat-pane--loading" aria-busy="true">
        <p>Loading conversation…</p>
      </div>
    );
  }

  return (
    <CopilotChat
      key={`${threadId}:${reloadNonce}`}
      className="app-chat"
      instructions={chatInstructions}
      labels={CHAT_LABELS}
      AssistantMessage={AssistantMessage}
      markdownTagRenderers={chatMarkdownTagRenderers}
    />
  );
}
