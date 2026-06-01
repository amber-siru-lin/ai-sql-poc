import type { SemanticLayerMode } from "../config";
import { useChatSession } from "../hooks/useChatSession";
import "./SessionPanel.css";

const AUDIT_BUCKET = "cta-poc-ai-sql-audit-dev-654654461736";

const MEMORY_COMMON: { title: string; detail: string }[] = [
  {
    title: "Follow-up context (LangGraph)",
    detail:
      "The API keeps this thread’s messages in RAM (MemorySaver) while uvicorn runs. Restarting the API clears follow-up memory; use the same thread ID after refresh only if chat snapshots restored your messages.",
  },
  {
    title: "Thread ID (browser)",
    detail:
      "Stored in localStorage (`ai-sql-poc-thread-id`). CopilotKit sends it on every run so retries and checkpoints stay on one thread.",
  },
  {
    title: "Chat snapshots (browser)",
    detail:
      "Up to 80 messages per thread in localStorage (`ai-sql-poc-chat-snapshots`) so the UI can restore text after refresh. Not a full server-side transcript store.",
  },
  {
    title: "Query audit log",
    detail: `Every completed run appends JSON to logs/audit/ and, when configured, S3 (${AUDIT_BUCKET}/audit/). Open Audit logs in the sidebar or use the button below.`,
  },
  {
    title: "Chat history (sidebar)",
    detail:
      "Past sessions are grouped by thread ID from the audit log (API runs only). Selecting one reuses that thread ID; server follow-ups apply only while the API still holds that checkpoint.",
  },
  {
    title: "SQL retries",
    detail: "Per-thread attempt counters live in API memory only until uvicorn restarts.",
  },
];

const MEMORY_LAYERS: Record<
  SemanticLayerMode,
  { title: string; detail: string }[]
> = {
  off: [...MEMORY_COMMON],
  wren: [
    ...MEMORY_COMMON,
    {
      title: "Wren semantic memory",
      detail:
        "NL↔SQL recall from `wren memory index` under wren/tpch/target/ (gitignored). Rebuild after MDL changes.",
    },
  ],
  cortex: [...MEMORY_COMMON],
};

type Props = {
  semanticLayerMode: SemanticLayerMode;
  threadId: string;
  onThreadIdChange: (nextId: string) => void;
  onViewAuditLogs?: () => void;
};

export function SessionPanel({
  semanticLayerMode,
  threadId,
  onThreadIdChange,
  onViewAuditLogs,
}: Props) {
  const {
    messageCount,
    isLoading,
    lastClearedAt,
    startNewConversation,
  } = useChatSession(threadId, onThreadIdChange);

  const shortThread =
    threadId.length > 12 ? `${threadId.slice(0, 8)}…${threadId.slice(-4)}` : threadId;

  return (
    <section className="session-panel" aria-label="Session and memory">
      <h2 className="session-panel__title">Session</h2>

      <dl className="session-panel__meta">
        <div>
          <dt>Thread</dt>
          <dd title={threadId}>
            <code>{shortThread}</code>
          </dd>
        </div>
        <div>
          <dt>Messages</dt>
          <dd>{messageCount}</dd>
        </div>
      </dl>

      <button
        type="button"
        className="session-panel__clear"
        disabled={isLoading}
        onClick={startNewConversation}
      >
        Clear conversation
      </button>
      {lastClearedAt ? (
        <p className="session-panel__cleared" role="status">
          New thread started — prior follow-up context on the server is no longer used.
        </p>
      ) : null}

      <h3 className="session-panel__subtitle">Where memory lives</h3>
      <ul className="session-panel__memory-list">
        {MEMORY_LAYERS[semanticLayerMode].map((item) => (
          <li key={item.title}>
            <strong>{item.title}</strong>
            <span>{item.detail}</span>
          </li>
        ))}
      </ul>

      {onViewAuditLogs ? (
        <button type="button" className="session-panel__audit-link" onClick={onViewAuditLogs}>
          View audit logs for this thread
        </button>
      ) : null}

      <p className="session-panel__footnote">
        Past sessions appear in the left sidebar. Full chat text is cached in this browser;
        each run is also logged to <code>logs/audit/</code> and optional S3. Server follow-up
        context still lives in API memory until restart.
      </p>
    </section>
  );
}
