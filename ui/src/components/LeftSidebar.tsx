import type {
  AppView,
  AuditConfig,
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

type Props = {
  apiStatus: string;
  auditStatus: AuditConfig | null;
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
};

export function LeftSidebar({
  apiStatus,
  auditStatus,
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
}: Props) {
  const apiOk = apiStatus === "connected";
  const auditConn = auditConnectionLabel(auditStatus);

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
