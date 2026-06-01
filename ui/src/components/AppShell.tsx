import { CopilotChat } from "@copilotkit/react-ui";

import type { AppView, SemanticLayerMode, SemanticLayerStatus } from "../config";
import type { AuditSession } from "../types/audit";
import { AuditLogsPage } from "./AuditLogsPage";
import { SemanticLayerPage } from "./SemanticLayerPage";
import { AssistantMessage } from "./AssistantMessage";
import { ChatSessionRestore } from "./ChatSessionRestore";
import { chatMarkdownTagRenderers } from "./chatMarkdownRenderers";
import { ContextSidebar } from "./ContextSidebar";
import { LeftSidebar } from "./LeftSidebar";
import "./AppShell.css";

const CHAT_LABELS = {
  title: "SQL Assistant",
  initial: "Ask a question about TPCH_SF1…",
} as const;

type Props = {
  apiStatus: string;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
  chatInstructions: string;
  threadId: string;
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
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
  chatInstructions,
  threadId,
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
          <div className="app-chat-pane">
            <ChatSessionRestore
              threadId={threadId}
              onSessionsChanged={onSessionsChanged}
            />
            <CopilotChat
              className="app-chat"
              instructions={chatInstructions}
              labels={CHAT_LABELS}
              AssistantMessage={AssistantMessage}
              markdownTagRenderers={chatMarkdownTagRenderers}
            />
          </div>
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
