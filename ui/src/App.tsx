import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

import { ActiveThreadFlushBridge } from "./components/ActiveThreadFlushBridge";
import { AppShell } from "./components/AppShell";
import { CopilotToolRenderers } from "./components/CopilotToolRenderers";
import { EditorActiveThreadFlushBridge } from "./components/EditorActiveThreadFlushBridge";
import {
  AGENT_ID,
  API_URL,
  COPILOT_RUNTIME_URL,
  EDITOR_AGENT_ID,
  type ApiStatusResponse,
  type AppView,
  type AuditConfig,
  type PostgresDockerStatus,
} from "./config";
import {
  loadStoredThreadId,
  SESSION_STORAGE_KEY,
} from "./hooks/useChatSession";
import { useChatSessions } from "./hooks/useChatSessions";
import {
  EDITOR_SESSION_STORAGE_KEY,
  loadEditorThreadId,
} from "./hooks/useEditorSession";
import { useEditorSessions } from "./hooks/useEditorSessions";
import { useSemanticLayerMode } from "./hooks/useSemanticLayerMode";
import { createEditorHttpAgent, type EditorAgentContext } from "./lib/editorHttpAgent";
import { createSemanticHttpAgent } from "./lib/httpAgent";
import {
  createSessionOnApi,
  migrateLocalSnapshotsOnce,
  setSessionsAvailableFromStatus,
} from "./lib/sessionApi";

const CHAT_INSTRUCTIONS_FALLBACK = `You are helping a business user explore their Snowflake dataset.
Use the active semantic layer mode (Off, Wren, or Cortex) as described in your system prompt.
Always explain the answer in plain English and show the final SQL.`;

export default function App() {
  const [apiStatusPayload, setApiStatusPayload] = useState<ApiStatusResponse | null>(null);
  const [apiStatus, setApiStatus] = useState<string>("checking…");
  const [semanticStatus, setSemanticStatus] =
    useState<ApiStatusResponse["semantic_layer"] | null>(null);
  const [auditStatus, setAuditStatus] = useState<AuditConfig | null>(null);
  const [postgresStatus, setPostgresStatus] = useState<PostgresDockerStatus | null>(null);
  const { mode: semanticLayerMode, setMode: setSemanticLayerMode } =
    useSemanticLayerMode(semanticStatus);
  const [threadId, setThreadId] = useState(loadStoredThreadId);
  const [reloadNonce, setReloadNonce] = useState(0);
  const threadIdRef = useRef(threadId);
  threadIdRef.current = threadId;
  const semanticLayerRef = useRef(semanticLayerMode);
  semanticLayerRef.current = semanticLayerMode;
  const flushActiveThreadRef = useRef<() => void>(() => {});
  const copilotOwnerThreadIdRef = useRef(threadId);
  const [editorThreadId, setEditorThreadId] = useState(loadEditorThreadId);
  const [editorReloadNonce, setEditorReloadNonce] = useState(0);
  const editorThreadIdRef = useRef(editorThreadId);
  editorThreadIdRef.current = editorThreadId;
  const flushEditorThreadRef = useRef<() => void>(() => {});
  const editorOwnerThreadIdRef = useRef(editorThreadId);
  const editorContextRef = useRef<EditorAgentContext>({ path: null, content: "" });
  const [activeView, setActiveView] = useState<AppView>("chat");
  const [auditThreadFilter, setAuditThreadFilter] = useState<string | undefined>();
  const { sessions, loading: sessionsLoading, error: sessionsError, refresh: refreshSessions } =
    useChatSessions();
  const {
    sessions: editorSessions,
    loading: editorSessionsLoading,
    error: editorSessionsError,
    refresh: refreshEditorSessions,
  } = useEditorSessions();

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ path: string; content: string }>).detail;
      if (detail?.path) {
        editorContextRef.current = {
          path: detail.path,
          content: detail.content ?? "",
        };
      }
    };
    window.addEventListener("semantic-editor-active-file", handler);
    return () => window.removeEventListener("semantic-editor-active-file", handler);
  }, []);

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
    const nextId = crypto.randomUUID();
    void createSessionOnApi(nextId, {
      title: "New chat",
      semanticLayer: semanticLayerMode,
    });
    selectThread(nextId);
  }, [selectThread, semanticLayerMode]);

  const selectEditorThread = useCallback(
    (nextId: string) => {
      flushEditorThreadRef.current();
      localStorage.setItem(EDITOR_SESSION_STORAGE_KEY, nextId);
      setActiveView("semantic");
      const session = editorSessions.find((s) => s.thread_id === nextId);
      if (session?.active_file) {
        window.dispatchEvent(
          new CustomEvent("semantic-editor-open", {
            detail: { path: session.active_file },
          }),
        );
      }
      if (nextId === editorThreadIdRef.current) {
        setEditorReloadNonce((n) => n + 1);
        return;
      }
      setEditorThreadId(nextId);
    },
    [editorSessions],
  );

  const onNewEditorChat = useCallback(() => {
    selectEditorThread(crypto.randomUUID());
  }, [selectEditorThread]);

  const prevSemanticMode = useRef(semanticLayerMode);
  useEffect(() => {
    if (prevSemanticMode.current === semanticLayerMode) return;
    prevSemanticMode.current = semanticLayerMode;
    selectThread(crypto.randomUUID());
  }, [semanticLayerMode, selectThread]);

  const chatInstructions = useMemo(() => {
    const dataset = apiStatusPayload?.dataset;
    if (!dataset) return CHAT_INSTRUCTIONS_FALLBACK;
    return `You are helping a business user explore the Snowflake dataset "${dataset}".
Use the active semantic layer mode (Off, Wren, or Cortex) as described in your system prompt.
Always explain the answer in plain English and show the final SQL.`;
  }, [apiStatusPayload?.dataset]);

  const refreshApiStatus = useCallback(() => {
    fetch(`${API_URL}/api/status`)
      .then((r) => r.json())
      .then((data: ApiStatusResponse) => {
        setApiStatusPayload(data);
        setApiStatus(data.status === "ok" ? "connected" : "unknown");
        setSemanticStatus(data.semantic_layer);
        setAuditStatus(data.audit ?? null);
        setPostgresStatus(data.postgres ?? null);
        setSessionsAvailableFromStatus(data.sessions ?? null);
        if (data.sessions?.available) {
          void migrateLocalSnapshotsOnce();
        }
      })
      .catch(() => {
        setApiStatusPayload(null);
        setApiStatus(`offline — start the API (${API_URL})`);
        setSemanticStatus(null);
        setAuditStatus(null);
        setPostgresStatus(null);
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
      [EDITOR_AGENT_ID]: createEditorHttpAgent(editorContextRef, editorThreadIdRef),
    }),
    // Stable agent instances — thread/mode read from refs on each request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  return (
    <CopilotKit
      key={semanticLayerMode}
      runtimeUrl={COPILOT_RUNTIME_URL}
      agents__unsafe_dev_only={agents as never}
      agent={AGENT_ID}
      showDevConsole={false}
      enableInspector={false}
    >
      <CopilotToolRenderers />
      <ActiveThreadFlushBridge
        threadId={threadId}
        flushRef={flushActiveThreadRef}
        copilotOwnerThreadIdRef={copilotOwnerThreadIdRef}
      />
      <EditorActiveThreadFlushBridge
        threadId={editorThreadId}
        flushRef={flushEditorThreadRef}
        editorOwnerThreadIdRef={editorOwnerThreadIdRef}
      />
      <AppShell
        apiStatus={apiStatus}
        apiStatusPayload={apiStatusPayload}
        auditStatus={auditStatus}
        postgresStatus={postgresStatus}
        semanticLayerMode={semanticLayerMode}
        semanticStatus={semanticStatus}
        onSemanticLayerChange={setSemanticLayerMode}
        chatInstructions={chatInstructions}
        threadId={threadId}
        reloadNonce={reloadNonce}
        copilotOwnerThreadIdRef={copilotOwnerThreadIdRef}
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
        editorThreadId={editorThreadId}
        editorReloadNonce={editorReloadNonce}
        editorOwnerThreadIdRef={editorOwnerThreadIdRef}
        onEditorThreadIdChange={selectEditorThread}
        onNewEditorChat={onNewEditorChat}
        onEditorSessionsChanged={refreshEditorSessions}
        editorSessions={editorSessions}
        editorSessionsLoading={editorSessionsLoading}
        editorSessionsError={editorSessionsError}
        onFlushChatThread={() => flushActiveThreadRef.current()}
        onFlushEditorThread={() => flushEditorThreadRef.current()}
      />
    </CopilotKit>
  );
}
