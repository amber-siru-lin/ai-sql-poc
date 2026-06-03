import type { MutableRefObject } from "react";
import { useCallback, useState } from "react";

import type {
  AppView,
  AuditConfig,
  ApiStatusResponse,
  PostgresDockerStatus,
  SemanticLayerMode,
  SemanticLayerStatus,
} from "../config";
import type { AuditSession } from "../types/audit";
import { AuditLogsPage } from "./AuditLogsPage";
import { ChatPane } from "./ChatPane";
import { ContextSidebar } from "./ContextSidebar";
import { LeftSidebar } from "./LeftSidebar";
import { SemanticEditorChat } from "./SemanticEditorChat";
import { SemanticLayerPage } from "./SemanticLayerPage";
import { loadRightSidebarOpen, saveRightSidebarOpen } from "../hooks/useRightSidebar";
import "./AppShell.css";

type Props = {
  apiStatus: string;
  apiStatusPayload: ApiStatusResponse | null;
  auditStatus: AuditConfig | null;
  postgresStatus: PostgresDockerStatus | null;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
  chatInstructions: string;
  threadId: string;
  reloadNonce: number;
  copilotOwnerThreadIdRef: MutableRefObject<string>;
  onThreadIdChange: (nextId: string) => void;
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  auditThreadFilter?: string;
  onOpenAuditForThread?: () => void;
  onNewChat: () => void;
  onSessionsChanged: () => void;
  sessions?: AuditSession[];
  sessionsLoading?: boolean;
  sessionsError?: string | null;
  editorThreadId: string;
  editorReloadNonce: number;
  editorOwnerThreadIdRef: MutableRefObject<string>;
  onEditorThreadIdChange: (nextId: string) => void;
  onNewEditorChat: () => void;
  onEditorSessionsChanged: () => void;
  editorSessions?: AuditSession[];
  editorSessionsLoading?: boolean;
  editorSessionsError?: string | null;
  onFlushChatThread?: () => void;
  onFlushEditorThread?: () => void;
};

export function AppShell({
  apiStatus,
  apiStatusPayload,
  auditStatus,
  postgresStatus,
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
  chatInstructions,
  threadId,
  reloadNonce,
  copilotOwnerThreadIdRef,
  onThreadIdChange,
  activeView,
  onViewChange,
  auditThreadFilter,
  onOpenAuditForThread,
  onNewChat,
  onSessionsChanged,
  sessions = [],
  sessionsLoading = false,
  sessionsError = null,
  editorThreadId,
  editorReloadNonce,
  editorOwnerThreadIdRef,
  onEditorThreadIdChange,
  onNewEditorChat,
  onEditorSessionsChanged,
  editorSessions = [],
  editorSessionsLoading = false,
  editorSessionsError = null,
  onFlushChatThread,
  onFlushEditorThread,
}: Props) {
  const [rightSidebarOpen, setRightSidebarOpen] = useState(loadRightSidebarOpen);
  const showRightRail = activeView === "chat" || activeView === "semantic";
  const rightRailLabel =
    activeView === "semantic" ? "Editor AI panel" : "Context panel";

  const toggleRightSidebar = useCallback(() => {
    setRightSidebarOpen((open) => {
      if (open) {
        if (activeView === "semantic") onFlushEditorThread?.();
        else if (activeView === "chat") onFlushChatThread?.();
      }
      const next = !open;
      saveRightSidebarOpen(next);
      return next;
    });
  }, [activeView, onFlushChatThread, onFlushEditorThread]);

  return (
    <div
      className={`app-layout${rightSidebarOpen && showRightRail ? "" : " app-layout--right-collapsed"}`}
    >
      <LeftSidebar
        apiStatus={apiStatus}
        apiStatusPayload={apiStatusPayload}
        auditStatus={auditStatus}
        postgresStatus={postgresStatus}
        semanticLayerMode={semanticLayerMode}
        semanticStatus={semanticStatus}
        onSemanticLayerChange={onSemanticLayerChange}
        activeView={activeView}
        onViewChange={onViewChange}
        threadId={threadId}
        onSelectSession={onThreadIdChange}
        onNewChat={onNewChat}
        sessions={sessions}
        sessionsLoading={sessionsLoading}
        sessionsError={sessionsError}
        onSessionsRefresh={onSessionsChanged}
        editorThreadId={editorThreadId}
        onSelectEditorSession={onEditorThreadIdChange}
        onNewEditorChat={onNewEditorChat}
        editorSessions={editorSessions}
        editorSessionsLoading={editorSessionsLoading}
        editorSessionsError={editorSessionsError}
        onEditorSessionsRefresh={onEditorSessionsChanged}
      />

      <main className="app-layout__main">
        {activeView === "chat" ? (
          <ChatPane
            threadId={threadId}
            reloadNonce={reloadNonce}
            chatInstructions={chatInstructions}
            datasetLabel={apiStatusPayload?.dataset}
            copilotOwnerThreadIdRef={copilotOwnerThreadIdRef}
            onSessionsChanged={onSessionsChanged}
          />
        ) : activeView === "audit" ? (
          <AuditLogsPage filterThreadId={auditThreadFilter} />
        ) : (
          <SemanticLayerPage activeSemanticMode={semanticLayerMode} />
        )}
      </main>

      {showRightRail ? (
        <div className="app-layout__right-rail">
          <button
            type="button"
            className="app-layout__right-toggle"
            onClick={toggleRightSidebar}
            aria-expanded={rightSidebarOpen}
            aria-controls="app-right-sidebar"
            title={rightSidebarOpen ? `Hide ${rightRailLabel}` : `Show ${rightRailLabel}`}
          >
            <span aria-hidden>{rightSidebarOpen ? "›" : "‹"}</span>
          </button>
          {rightSidebarOpen ? (
            <div id="app-right-sidebar" className="app-layout__right-panel">
              {activeView === "chat" ? (
                <ContextSidebar
                  semanticLayerMode={semanticLayerMode}
                  threadId={threadId}
                  apiStatusPayload={apiStatusPayload}
                  auditStatus={auditStatus}
                  onOpenAuditForThread={onOpenAuditForThread}
                />
              ) : (
                <SemanticEditorChat
                  threadId={editorThreadId}
                  reloadNonce={editorReloadNonce}
                  editorOwnerThreadIdRef={editorOwnerThreadIdRef}
                  onSessionsChanged={onEditorSessionsChanged}
                />
              )}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
