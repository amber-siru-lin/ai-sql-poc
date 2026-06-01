import type {
  AppView,
  AuditConfig,
  SemanticLayerMode,
  SemanticLayerStatus,
} from "../config";
import type { AuditSession } from "../types/audit";
import { AuditLogsPage } from "./AuditLogsPage";
import { ChatPane } from "./ChatPane";
import { ContextSidebar } from "./ContextSidebar";
import { LeftSidebar } from "./LeftSidebar";
import { SemanticLayerPage } from "./SemanticLayerPage";
import "./AppShell.css";

type Props = {
  apiStatus: string;
  auditStatus: AuditConfig | null;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
  chatInstructions: string;
  threadId: string;
  reloadNonce: number;
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
};

export function AppShell({
  apiStatus,
  auditStatus,
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
  chatInstructions,
  threadId,
  reloadNonce,
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
}: Props) {
  return (
    <div className="app-layout">
      <LeftSidebar
        apiStatus={apiStatus}
        auditStatus={auditStatus}
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
      />

      <main className="app-layout__main">
        {activeView === "chat" ? (
          <ChatPane
            threadId={threadId}
            reloadNonce={reloadNonce}
            chatInstructions={chatInstructions}
            onSessionsChanged={onSessionsChanged}
          />
        ) : activeView === "audit" ? (
          <AuditLogsPage filterThreadId={auditThreadFilter} />
        ) : (
          <SemanticLayerPage activeSemanticMode={semanticLayerMode} />
        )}
      </main>

      {activeView === "chat" ? (
        <ContextSidebar
          semanticLayerMode={semanticLayerMode}
          threadId={threadId}
          onThreadIdChange={onThreadIdChange}
          onOpenAuditForThread={onOpenAuditForThread}
        />
      ) : null}
    </div>
  );
}
