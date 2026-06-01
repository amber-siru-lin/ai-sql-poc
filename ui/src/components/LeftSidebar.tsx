import type { AppView, SemanticLayerMode, SemanticLayerStatus } from "../config";
import { ChatHistoryList } from "./ChatHistoryList";
import { SemanticLayerToggle } from "./SemanticLayerToggle";
import "./LeftSidebar.css";

type Props = {
  apiStatus: string;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  threadId: string;
  onSelectSession: (threadId: string) => void;
  onNewChat: () => void;
  sessions: import("../types/audit").AuditSession[];
  sessionsLoading: boolean;
  sessionsError: string | null;
  onSessionsRefresh: () => void;
};

export function LeftSidebar({
  apiStatus,
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
  activeView,
  onViewChange,
  threadId,
  onSelectSession,
  onNewChat,
  sessions,
  sessionsLoading,
  sessionsError,
  onSessionsRefresh,
}: Props) {
  const apiOk = apiStatus === "connected";

  return (
    <aside className="left-sidebar" aria-label="Workspace">
      <div className="left-sidebar__brand">
        <p className="left-sidebar__eyebrow">AI SQL POC</p>
        <h1 className="left-sidebar__title">TPCH Assistant</h1>
        <p className="left-sidebar__subtitle">Natural language → Snowflake</p>
      </div>

      <nav className="left-sidebar__nav" aria-label="Main">
        <button
          type="button"
          className={`left-sidebar__nav-btn${activeView === "chat" ? " left-sidebar__nav-btn--active" : ""}`}
          onClick={() => onViewChange("chat")}
        >
          Chat
        </button>
        <button
          type="button"
          className={`left-sidebar__nav-btn${activeView === "audit" ? " left-sidebar__nav-btn--active" : ""}`}
          onClick={() => onViewChange("audit")}
        >
          Audit logs
        </button>
      </nav>

      <section className="left-sidebar__section">
        <h2 className="left-sidebar__section-title">Semantic layer</h2>
        <SemanticLayerToggle
          mode={semanticLayerMode}
          status={semanticStatus}
          onChange={onSemanticLayerChange}
        />
      </section>

      <section className="left-sidebar__section">
        <h2 className="left-sidebar__section-title">Connection</h2>
        <ul className="left-sidebar__status-list">
          <li>
            <span
              className={`status-dot status-dot--${apiOk ? "ok" : "warn"}`}
              aria-hidden
            />
            API {apiStatus}
          </li>
          <li>
            <span className="status-dot status-dot--ok" aria-hidden />
            Nova Pro · TPCH_SF1
          </li>
        </ul>
      </section>

      <section className="left-sidebar__section left-sidebar__section--grow">
        {activeView === "chat" ? (
          <ChatHistoryList
            activeThreadId={threadId}
            onSelectSession={onSelectSession}
            onNewChat={onNewChat}
          />
        ) : (
          <>
            <h2 className="left-sidebar__section-title">Chat history</h2>
            <p className="left-sidebar__placeholder">
              Switch to <strong>Chat</strong> to browse past sessions. Sessions are
              grouped from the query audit log.
            </p>
          </>
        )}
      </section>
    </aside>
  );
}
