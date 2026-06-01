import type { MutableRefObject } from "react";
import { CopilotChatConfigurationProvider } from "@copilotkit/react-core/v2";
import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { AssistantMessage } from "./AssistantMessage";
import { chatMarkdownTagRenderers } from "./chatMarkdownRenderers";
import { EDITOR_AGENT_ID } from "../config";
import { useEditorAgent } from "../hooks/useEditorAgent";
import type { StoredChatMessage } from "../lib/chatPersistence";
import {
  applyThreadTranscript,
  transcriptsMatch,
} from "../lib/chatPersistence";
import { resolveEditorThreadMessages } from "../lib/resolveEditorThreadMessages";
import "./SemanticEditorChat.css";

const EDITOR_CHAT_LABELS = {
  title: "Editor AI",
  initial: "Ask about MDL edits, join failures, or relationship fixes…",
} as const;

const EDITOR_INSTRUCTIONS = `You help edit the semantic layer (Wren MDL YAML, relationships, schema markdown).
Propose diffs before writing files. Use audit logs to explain failed joins.`;

type Props = {
  threadId: string;
  reloadNonce: number;
  editorOwnerThreadIdRef: MutableRefObject<string>;
  onSessionsChanged?: () => void;
};

export function SemanticEditorChat({
  threadId,
  reloadNonce,
  editorOwnerThreadIdRef,
  onSessionsChanged,
}: Props) {
  const { agent } = useEditorAgent({ watchMessages: true });
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
      const resolved = await resolveEditorThreadMessages(threadId);
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
    applyThreadTranscript(agent, loaded, threadId, editorOwnerThreadIdRef);
    prevCountRef.current = loaded.length;
  }, [threadId, reloadNonce, loaded, agent, editorOwnerThreadIdRef]);

  // CopilotChat connectAgent can restore stale messages from the shared agent store.
  useEffect(() => {
    if (loaded === null || !agent) return;

    const reapplyIfStale = () => {
      if (editorOwnerThreadIdRef.current !== threadId) return;
      if (transcriptsMatch(agent.messages, loaded)) return;
      applyThreadTranscript(agent, loaded, threadId, editorOwnerThreadIdRef);
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
  }, [loaded, threadId, agent, editorOwnerThreadIdRef]);

  useEffect(() => {
    if (loaded === null || !agent) return;
    if (threadId !== editorOwnerThreadIdRef.current) return;
    const count = agent.messages?.length ?? 0;
    if (agent.isRunning || count === 0) return;
    if (count > prevCountRef.current) {
      onSessionsChangedRef.current?.();
    }
    prevCountRef.current = count;
  }, [agent?.messages, agent?.isRunning, loaded, threadId, agent, editorOwnerThreadIdRef]);

  return (
    <aside className="semantic-editor-chat" aria-label="Semantic layer editor AI">
      {isRestoring ? (
        <div className="semantic-editor-chat__loading" aria-busy="true">
          <p>Loading editor conversation…</p>
        </div>
      ) : null}
      {loaded !== null ? (
        <CopilotChatConfigurationProvider
          key={threadId}
          agentId={EDITOR_AGENT_ID}
          threadId={threadId}
          hasExplicitThreadId
        >
          <CopilotChat
            className="semantic-editor-chat__pane"
            instructions={EDITOR_INSTRUCTIONS}
            labels={EDITOR_CHAT_LABELS}
            AssistantMessage={AssistantMessage}
            markdownTagRenderers={chatMarkdownTagRenderers}
          />
        </CopilotChatConfigurationProvider>
      ) : null}
    </aside>
  );
}
