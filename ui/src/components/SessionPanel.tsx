import type { SemanticLayerMode } from "../config";
import { useSqlAgent } from "../hooks/useSqlAgent";
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
    title: "Query audit log (S3)",
    detail: `Each completed run writes one JSON file to S3 (${AUDIT_BUCKET}/audit/). Check Connection → Audit log (S3) for sync status. Open Audit logs in the sidebar or use the button below.`,
  },
  {
    title: "Chat history (sidebar)",
    detail:
      "Past sessions are grouped by thread ID from the audit log (API runs only). Selecting one reuses that thread ID; server follow-ups apply only while the API still holds that checkpoint. Use + New to start a fresh session.",
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
  onViewAuditLogs?: () => void;
};

export function SessionPanel({
  semanticLayerMode,
  threadId,
  onViewAuditLogs,
}: Props) {
  const { agent } = useSqlAgent({ watchMessages: true });
  const messageCount = agent?.messages?.length ?? 0;

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
        Past sessions appear in the left sidebar (from S3 audit). Chat text is cached in this
        browser only. Server follow-up context still lives in API memory until restart.
      </p>
    </section>
  );
}
