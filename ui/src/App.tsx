import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

import { AppShell } from "./components/AppShell";
import { CopilotToolRenderers } from "./components/CopilotToolRenderers";
import {
  AGENT_ID,
  API_URL,
  COPILOT_RUNTIME_URL,
  type ApiStatusResponse,
  type AppView,
} from "./config";
import {
  loadStoredThreadId,
  SESSION_STORAGE_KEY,
} from "./hooks/useChatSession";
import { useChatSessions } from "./hooks/useChatSessions";
import { useSemanticLayerMode } from "./hooks/useSemanticLayerMode";
import { createSemanticHttpAgent } from "./lib/httpAgent";

const CHAT_INSTRUCTIONS = `You are helping a business user explore the Snowflake TPCH_SF1 dataset.
Use the active semantic layer mode (Off, Wren, or Cortex) as described in your system prompt.
Always explain the answer in plain English and show the final SQL.`;

export default function App() {
  const [apiStatus, setApiStatus] = useState<string>("checking…");
  const [semanticStatus, setSemanticStatus] =
    useState<ApiStatusResponse["semantic_layer"] | null>(null);
  const { mode: semanticLayerMode, setMode: setSemanticLayerMode } =
    useSemanticLayerMode(semanticStatus);
  const [threadId, setThreadId] = useState(loadStoredThreadId);
  const [activeView, setActiveView] = useState<AppView>("chat");
  const [auditThreadFilter, setAuditThreadFilter] = useState<string | undefined>();
  const { sessions, loading: sessionsLoading, error: sessionsError, refresh: refreshSessions } =
    useChatSessions();

  const handleViewChange = useCallback((view: AppView) => {
    setActiveView(view);
    if (view === "chat") setAuditThreadFilter(undefined);
  }, []);

  const openAuditForThread = useCallback(() => {
    setAuditThreadFilter(threadId);
    setActiveView("audit");
  }, [threadId]);

  const onThreadIdChange = useCallback((nextId: string) => {
    setThreadId(nextId);
    localStorage.setItem(SESSION_STORAGE_KEY, nextId);
    setActiveView("chat");
  }, []);

  const onNewChat = useCallback(() => {
    onThreadIdChange(crypto.randomUUID());
  }, [onThreadIdChange]);

  const prevSemanticMode = useRef(semanticLayerMode);
  useEffect(() => {
    if (prevSemanticMode.current === semanticLayerMode) return;
    prevSemanticMode.current = semanticLayerMode;
    onThreadIdChange(crypto.randomUUID());
  }, [semanticLayerMode, onThreadIdChange]);

  useEffect(() => {
    fetch(`${API_URL}/api/status`)
      .then((r) => r.json())
      .then((data: ApiStatusResponse) => {
        setApiStatus(data.status === "ok" ? "connected" : "unknown");
        setSemanticStatus(data.semantic_layer);
      })
      .catch(() => {
        setApiStatus("offline — start the API on port 8000");
        setSemanticStatus(null);
      });
  }, []);

  const agents = useMemo(
    () => ({
      [AGENT_ID]: createSemanticHttpAgent(semanticLayerMode, threadId),
    }),
    [semanticLayerMode, threadId],
  );

  return (
    <CopilotKit
      key={`${semanticLayerMode}-${threadId}`}
      runtimeUrl={COPILOT_RUNTIME_URL}
      agents__unsafe_dev_only={agents as never}
      agent={AGENT_ID}
      threadId={threadId}
      showDevConsole={false}
      enableInspector={false}
    >
      <CopilotToolRenderers />
      <AppShell
        apiStatus={apiStatus}
        semanticLayerMode={semanticLayerMode}
        semanticStatus={semanticStatus}
        onSemanticLayerChange={setSemanticLayerMode}
        chatInstructions={CHAT_INSTRUCTIONS}
        threadId={threadId}
        onThreadIdChange={onThreadIdChange}
        activeView={activeView}
        onViewChange={handleViewChange}
        auditThreadFilter={auditThreadFilter}
        onOpenAuditForThread={openAuditForThread}
        onNewChat={onNewChat}
        onSessionsChanged={refreshSessions}
      />
    </CopilotKit>
  );
}
