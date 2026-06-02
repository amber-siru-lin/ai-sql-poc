import type { AuditSession } from "../types/audit";
import "./ChatHistoryList.css";

function formatSessionTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function truncateTitle(title: string | undefined, max = 52): string {
  const t = (title ?? "").trim();
  if (!t) return "(untitled session)";
  if (t.length <= max) return t;
  return `${t.slice(0, max - 1)}…`;
}

type Props = {
  activeThreadId: string;
  onSelectSession: (threadId: string) => void;
  onNewChat: () => void;
  sessions?: AuditSession[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  /** Sidebar list variant — defaults to NL→SQL chat. */
  variant?: "chat" | "editor";
};

const VARIANT_COPY = {
  chat: {
    title: "Chat history",
    empty: "No sessions yet. Click + New or ask a question — history is saved in Postgres.",
    newTitle: "Start a new conversation",
  },
  editor: {
    title: "Editor history",
    empty: "No editor sessions yet. Ask the Editor AI about MDL fixes — runs are saved to the audit log.",
    newTitle: "Start a new editor conversation",
  },
} as const;

export function ChatHistoryList({
  activeThreadId,
  onSelectSession,
  onNewChat,
  sessions = [],
  loading = false,
  error = null,
  onRefresh,
  variant = "chat",
}: Props) {
  const safeSessions = sessions ?? [];
  const copy = VARIANT_COPY[variant];

  return (
    <section className="chat-history" aria-label={copy.title}>
      <div className="chat-history__head">
        <h2 className="chat-history__title">{copy.title}</h2>
        <button
          type="button"
          className="chat-history__new"
          onClick={onNewChat}
          title={copy.newTitle}
        >
          + New
        </button>
      </div>

      {loading ? (
        <p className="chat-history__hint">Loading sessions…</p>
      ) : error ? (
        <p className="chat-history__hint chat-history__hint--error">{error}</p>
      ) : safeSessions.length === 0 ? (
        <p className="chat-history__hint">{copy.empty}</p>
      ) : (
        <ul className="chat-history__list">
          {safeSessions.map((session: AuditSession) => {
            const active = session.thread_id === activeThreadId;
            const fileHint =
              variant === "editor" && session.active_file
                ? ` · ${session.active_file.split("/").pop()}`
                : "";
            const layerHint =
              variant === "chat" && session.semantic_layer
                ? ` · ${session.semantic_layer}`
                : "";
            return (
              <li key={session.thread_id}>
                <button
                  type="button"
                  className={`chat-history__item${active ? " chat-history__item--active" : ""}`}
                  onClick={() => onSelectSession(session.thread_id)}
                  title={session.title}
                >
                  <span className="chat-history__item-title">
                    {truncateTitle(session.title)}
                  </span>
                  <span className="chat-history__item-meta">
                    {formatSessionTime(session.last_timestamp)}
                    {session.run_count > 1 ? ` · ${session.run_count} runs` : ""}
                    {layerHint}
                    {fileHint}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {onRefresh ? (
        <button
          type="button"
          className="chat-history__refresh"
          onClick={() => void onRefresh()}
          disabled={loading}
        >
          Refresh
        </button>
      ) : null}
    </section>
  );
}
