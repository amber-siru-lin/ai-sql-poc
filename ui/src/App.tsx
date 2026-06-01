import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

import { ActiveThreadFlushBridge } from "./components/ActiveThreadFlushBridge";
import { AppShell } from "./components/AppShell";
import { CopilotToolRenderers } from "./components/CopilotToolRenderers";
import {
  AGENT_ID,
  API_URL,
  COPILOT_RUNTIME_URL,
  type ApiStatusResponse,
  type AppView,
  type AuditConfig,
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
  const [auditStatus, setAuditStatus] = useState<AuditConfig | null>(null);
  const { mode: semanticLayerMode, setMode: setSemanticLayerMode } =
    useSemanticLayerMode(semanticStatus);
  const [threadId, setThreadId] = useState(loadStoredThreadId);
  const [reloadNonce, setReloadNonce] = useState(0);
  const threadIdRef = useRef(threadId);
  threadIdRef.current = threadId;
  const semanticLayerRef = useRef(semanticLayerMode);
  semanticLayerRef.current = semanticLayerMode;
  const flushActiveThreadRef = useRef<() => void>(() => {});
  const [activeView, setActiveView] = useState<AppView>("chat");
  const [auditThreadFilter, setAuditThreadFilter] = useState<string | undefined>();
  const { sessions, loading: sessionsLoading, error: sessionsError, refresh: refreshSessions } =
    useChatSessions();

  const handleViewChange = useCallback((view: AppView) => {
    setActiveView(view);
    if (view !== "audit") setAuditThreadFilter(undefined);
  }, []);

  const openAuditForThread = useCallback(() => {
    setAuditThreadFilter(threadId);
    setActiveView("audit");
  }, [threadId]);

  /** Save outgoing thread, then switch or reload the selected session. */
  const selectThread = useCallback((nextId: string) => {
    flushActiveThreadRef.current();
    localStorage.setItem(SESSION_STORAGE_KEY, nextId);
    setActiveView("chat");
    if (nextId === threadIdRef.current) {
      setReloadNonce((n) => n + 1);
      return;
    }
    setThreadId(nextId);
  }, []);

  const onNewChat = useCallback(() => {
    selectThread(crypto.randomUUID());
  }, [selectThread]);

  const prevSemanticMode = useRef(semanticLayerMode);
  useEffect(() => {
    if (prevSemanticMode.current === semanticLayerMode) return;
    prevSemanticMode.current = semanticLayerMode;
    selectThread(crypto.randomUUID());
  }, [semanticLayerMode, selectThread]);

  const refreshApiStatus = useCallback(() => {
    fetch(`${API_URL}/api/status`)
      .then((r) => r.json())
      .then((data: ApiStatusResponse) => {
        setApiStatus(data.status === "ok" ? "connected" : "unknown");
        setSemanticStatus(data.semantic_layer);
        setAuditStatus(data.audit ?? null);
      })
      .catch(() => {
        setApiStatus("offline — start the API on port 8000");
        setSemanticStatus(null);
        setAuditStatus(null);
      });
  }, []);

  useEffect(() => {
    refreshApiStatus();
    const id = window.setInterval(refreshApiStatus, 45_000);
    return () => window.clearInterval(id);
  }, [refreshApiStatus]);

  const agents = useMemo(
    () => ({
      [AGENT_ID]: createSemanticHttpAgent(semanticLayerRef, threadIdRef),
    }),
    // Stable agent instance — thread/mode read from refs on each request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  return (
    <CopilotKit
      key={semanticLayerMode}
      runtimeUrl={COPILOT_RUNTIME_URL}
      threadId={threadId}
      agents__unsafe_dev_only={agents as never}
      agent={AGENT_ID}
      showDevConsole={false}
      enableInspector={false}
    >
      <CopilotToolRenderers />
      <ActiveThreadFlushBridge threadId={threadId} flushRef={flushActiveThreadRef} />
      <AppShell
        apiStatus={apiStatus}
        auditStatus={auditStatus}
        semanticLayerMode={semanticLayerMode}
        semanticStatus={semanticStatus}
        onSemanticLayerChange={setSemanticLayerMode}
        chatInstructions={CHAT_INSTRUCTIONS}
        threadId={threadId}
        reloadNonce={reloadNonce}
        onThreadIdChange={selectThread}
        activeView={activeView}
        onViewChange={handleViewChange}
        auditThreadFilter={auditThreadFilter}
        onOpenAuditForThread={openAuditForThread}
        onNewChat={onNewChat}
        onSessionsChanged={refreshSessions}
        sessions={sessions}
        sessionsLoading={sessionsLoading}
        sessionsError={sessionsError}
      />
    </CopilotKit>
  );
}
