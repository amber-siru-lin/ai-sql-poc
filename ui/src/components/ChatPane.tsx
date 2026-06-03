import type { MutableRefObject } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { AssistantMessage } from "./AssistantMessage";
import { chatMarkdownTagRenderers } from "./chatMarkdownRenderers";
import { resolveThreadMessages } from "../lib/resolveThreadMessages";
import type { StoredChatMessage } from "../lib/chatPersistence";
import {
  applyThreadTranscript,
  transcriptsMatch,
} from "../lib/chatPersistence";
import { useSqlAgent } from "../hooks/useSqlAgent";
import "./ChatPane.css";

type Props = {
  threadId: string;
  /** Bump to reload the same thread from storage/audit (re-click in sidebar). */
  reloadNonce: number;
  chatInstructions: string;
  datasetLabel?: string;
  copilotOwnerThreadIdRef: MutableRefObject<string>;
  onSessionsChanged?: () => void;
};

export function ChatPane({
  threadId,
  reloadNonce,
  chatInstructions,
  datasetLabel,
  copilotOwnerThreadIdRef,
  onSessionsChanged,
}: Props) {
  const { agent } = useSqlAgent({ watchMessages: true });
  const [loaded, setLoaded] = useState<StoredChatMessage[] | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);
  const onSessionsChangedRef = useRef(onSessionsChanged);
  const chatLabels = useMemo(
    () => ({
      title: "SQL Assistant",
      initial: datasetLabel
        ? `Ask a question about ${datasetLabel}…`
        : "Ask a question about your Snowflake data…",
    }),
    [datasetLabel],
  );
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
    applyThreadTranscript(agent, loaded, threadId, copilotOwnerThreadIdRef);
    prevCountRef.current = loaded.length;
  }, [threadId, reloadNonce, loaded, agent, copilotOwnerThreadIdRef]);

  useEffect(() => {
    if (loaded === null || !agent) return;

    const reapplyIfStale = () => {
      if (copilotOwnerThreadIdRef.current !== threadId) return;
      if (transcriptsMatch(agent.messages, loaded)) return;
      applyThreadTranscript(agent, loaded, threadId, copilotOwnerThreadIdRef);
      prevCountRef.current = loaded.length;
    };

    const t0 = window.setTimeout(reapplyIfStale, 0);
    const t1 = window.setTimeout(reapplyIfStale, 120);
    const t2 = window.setTimeout(reapplyIfStale, 300);
    return () => {
      window.clearTimeout(t0);
      window.clearTimeout(t1);
      window.clearTimeout(t2);
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
      {loaded !== null ? (
        <CopilotChat
          key={threadId}
          className="app-chat"
          instructions={chatInstructions}
          labels={chatLabels}
          AssistantMessage={AssistantMessage}
          markdownTagRenderers={chatMarkdownTagRenderers}
        />
      ) : null}
    </div>
  );
}
