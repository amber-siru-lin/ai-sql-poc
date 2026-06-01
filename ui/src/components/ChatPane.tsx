import type { MutableRefObject } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { AssistantMessage } from "./AssistantMessage";
import { chatMarkdownTagRenderers } from "./chatMarkdownRenderers";
import { resolveThreadMessages } from "../lib/resolveThreadMessages";
import type { StoredChatMessage } from "../lib/chatPersistence";
import { useSqlAgent } from "../hooks/useSqlAgent";
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
  copilotOwnerThreadIdRef: MutableRefObject<string>;
  onSessionsChanged?: () => void;
};

function applyThreadMessages(
  agent: NonNullable<ReturnType<typeof useSqlAgent>["agent"]>,
  loaded: StoredChatMessage[],
  threadId: string,
  copilotOwnerThreadIdRef: MutableRefObject<string>,
) {
  agent.setMessages(loaded);
  copilotOwnerThreadIdRef.current = threadId;
}

export function ChatPane({
  threadId,
  reloadNonce,
  chatInstructions,
  copilotOwnerThreadIdRef,
  onSessionsChanged,
}: Props) {
  const { agent } = useSqlAgent({ watchMessages: true });
  const [loaded, setLoaded] = useState<StoredChatMessage[] | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);
  const onSessionsChangedRef = useRef(onSessionsChanged);
  onSessionsChangedRef.current = onSessionsChanged;
  const prevCountRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    setLoaded(null);
    setIsRestoring(true);

    void (async () => {
      const resolved = await resolveThreadMessages(threadId);
      if (!cancelled) {
        setLoaded(resolved);
        setIsRestoring(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [threadId, reloadNonce]);

  useLayoutEffect(() => {
    if (loaded === null || !agent) return;
    applyThreadMessages(agent, loaded, threadId, copilotOwnerThreadIdRef);
    prevCountRef.current = loaded.length;
  }, [threadId, reloadNonce, loaded, agent, copilotOwnerThreadIdRef]);

  // CopilotChat's useCopilotChatInternal connectAgent clears messages once on mount.
  useEffect(() => {
    if (loaded === null || loaded.length === 0 || !agent) return;

    const reapplyIfCleared = () => {
      if (copilotOwnerThreadIdRef.current !== threadId) return;
      if ((agent.messages?.length ?? 0) >= loaded.length) return;
      applyThreadMessages(agent, loaded, threadId, copilotOwnerThreadIdRef);
      prevCountRef.current = loaded.length;
    };

    const t0 = window.setTimeout(reapplyIfCleared, 0);
    const t1 = window.setTimeout(reapplyIfCleared, 120);
    return () => {
      window.clearTimeout(t0);
      window.clearTimeout(t1);
    };
  }, [loaded, threadId, agent, copilotOwnerThreadIdRef]);

  useEffect(() => {
    if (loaded === null || !agent) return;
    if (threadId !== copilotOwnerThreadIdRef.current) return;
    const count = agent.messages?.length ?? 0;
    if (agent.isRunning || count === 0) return;
    if (count > prevCountRef.current) {
      onSessionsChangedRef.current?.();
    }
    prevCountRef.current = count;
  }, [agent?.messages, agent?.isRunning, loaded, threadId, agent, copilotOwnerThreadIdRef]);

  return (
    <div className="chat-pane">
      {isRestoring ? (
        <div className="chat-pane__loading" aria-busy="true">
          <p>Loading conversation…</p>
        </div>
      ) : null}
      <CopilotChat
        className="app-chat"
        instructions={chatInstructions}
        labels={CHAT_LABELS}
        AssistantMessage={AssistantMessage}
        markdownTagRenderers={chatMarkdownTagRenderers}
      />
    </div>
  );
}
