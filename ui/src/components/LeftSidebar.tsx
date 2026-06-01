import type {
  AppView,
  AuditConfig,
  PostgresDockerStatus,
  SemanticLayerMode,
  SemanticLayerStatus,
} from "../config";
import type { AuditSession } from "../types/audit";
import { ChatHistoryList } from "./ChatHistoryList";
import { SemanticLayerToggle } from "./SemanticLayerToggle";
import "./LeftSidebar.css";

function auditConnectionLabel(audit: AuditConfig | null): {
  text: string;
  tone: "ok" | "warn";
  title?: string;
} {
  if (!audit?.s3_bucket) {
    return { text: "Audit log (S3) not configured", tone: "warn" };
  }
  if (audit.s3_status === "ok") {
    return {
      text: "Audit log (S3) connected",
      tone: "ok",
      title: audit.s3_message ?? undefined,
    };
  }
  if (audit.s3_status === "error") {
    return {
      text: "Audit log (S3) unavailable",
      tone: "warn",
      title: audit.s3_message ?? "S3 write or read failed",
    };
  }
  return { text: "Audit log (S3) checking…", tone: "warn" };
}

function postgresConnectionLabel(postgres: PostgresDockerStatus | null): {
  text: string;
  tone: "ok" | "warn";
  title?: string;
} {
  if (!postgres) {
    return { text: "Postgres (Docker) checking…", tone: "warn" };
  }
  if (postgres.status === "connected") {
    return {
      text: "Postgres (Docker) connected",
      tone: "ok",
      title: postgres.message,
    };
  }
  if (postgres.status === "not_configured") {
    return {
      text: "Postgres (Docker) not configured",
      tone: "warn",
      title: postgres.message,
    };
  }
  return {
    text: "Postgres (Docker) disconnected",
    tone: "warn",
    title: postgres.message,
  };
}

type Props = {
  apiStatus: string;
  auditStatus: AuditConfig | null;
  postgresStatus: PostgresDockerStatus | null;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  threadId: string;
  onSelectSession: (threadId: string) => void;
  onNewChat: () => void;
  sessions?: AuditSession[];
  sessionsLoading?: boolean;
  sessionsError?: string | null;
  onSessionsRefresh?: () => void;
  editorThreadId?: string;
  onSelectEditorSession?: (threadId: string) => void;
  onNewEditorChat?: () => void;
  editorSessions?: AuditSession[];
  editorSessionsLoading?: boolean;
  editorSessionsError?: string | null;
  onEditorSessionsRefresh?: () => void;
};

export function LeftSidebar({
  apiStatus,
  auditStatus,
  postgresStatus,
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
  activeView,
  onViewChange,
  threadId,
  onSelectSession,
  onNewChat,
  sessions = [],
  sessionsLoading = false,
  sessionsError = null,
  onSessionsRefresh,
  editorThreadId = "",
  onSelectEditorSession,
  onNewEditorChat,
  editorSessions = [],
  editorSessionsLoading = false,
  editorSessionsError = null,
  onEditorSessionsRefresh,
}: Props) {
  const apiOk = apiStatus === "connected";
  const auditConn = auditConnectionLabel(auditStatus);
  const postgresConn = postgresConnectionLabel(postgresStatus);

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
        <button
          type="button"
          className={`left-sidebar__nav-btn${activeView === "semantic" ? " left-sidebar__nav-btn--active" : ""}`}
          onClick={() => onViewChange("semantic")}
        >
          Semantic layer
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
          <li title={auditConn.title}>
            <span
              className={`status-dot status-dot--${auditConn.tone}`}
              aria-hidden
            />
            {auditConn.text}
          </li>
          <li title={postgresConn.title}>
            <span
              className={`status-dot status-dot--${postgresConn.tone}`}
              aria-hidden
            />
            {postgresConn.text}
          </li>
        </ul>
      </section>

      <section className="left-sidebar__section left-sidebar__section--grow">
        {activeView === "chat" ? (
          <ChatHistoryList
            activeThreadId={threadId}
            onSelectSession={onSelectSession}
            onNewChat={onNewChat}
            sessions={sessions}
            loading={sessionsLoading}
            error={sessionsError}
            onRefresh={onSessionsRefresh}
            variant="chat"
          />
        ) : activeView === "semantic" ? (
          <ChatHistoryList
            activeThreadId={editorThreadId}
            onSelectSession={onSelectEditorSession ?? (() => {})}
            onNewChat={onNewEditorChat ?? (() => {})}
            sessions={editorSessions}
            loading={editorSessionsLoading}
            error={editorSessionsError}
            onRefresh={onEditorSessionsRefresh}
            variant="editor"
          />
        ) : (
          <>
            <h2 className="left-sidebar__section-title">Chat history</h2>
            <p className="left-sidebar__placeholder">
              Switch to <strong>Chat</strong> or <strong>Semantic layer</strong> to
              browse session history.
            </p>
          </>
        )}
      </section>
    </aside>
  );
}
