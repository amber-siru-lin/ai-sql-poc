import { isWrenToolError } from "../utils/parseWrenToolResult";
import "./SqlToolResultCard.css";

type Props = {
  question?: string;
  memoryText?: string;
  status: string;
};

const MEMORY_PREVIEW_CHARS = 4000;

export function WrenMemoryCard({ question, memoryText, status }: Props) {
  const loading = !String(status).toLowerCase().includes("complete");

  if (loading) {
    return (
      <div className="sql-tool-card sql-tool-card--loading sql-tool-card--wren">
        <ToolCardHeader title="Wren · memory" status={status} />
        {question ? <p className="sql-tool-card__question">{question}</p> : null}
        <span className="sql-tool-card__status-text">Fetching MDL context…</span>
      </div>
    );
  }

  const text = memoryText ?? "";
  if (!text) {
    return (
      <div className="sql-tool-card sql-tool-card--wren">
        <ToolCardHeader title="Wren · memory" status={status} />
        <p className="sql-tool-card__empty">No memory context returned.</p>
      </div>
    );
  }

  if (isWrenToolError(text)) {
    return (
      <div className="sql-tool-card sql-tool-card--error sql-tool-card--wren">
        <ToolCardHeader title="Wren · memory" status={status} />
        {question ? <p className="sql-tool-card__question">{question}</p> : null}
        <pre className="sql-tool-card__raw">{text}</pre>
      </div>
    );
  }

  const truncated = text.length > MEMORY_PREVIEW_CHARS;
  const preview = truncated ? `${text.slice(0, MEMORY_PREVIEW_CHARS)}…` : text;

  return (
    <div className="sql-tool-card sql-tool-card--wren">
      <ToolCardHeader title="Wren · memory" status={status} />
      {question ? <p className="sql-tool-card__question">{question}</p> : null}
      <pre className="sql-tool-card__raw">{preview}</pre>
      {truncated ? (
        <p className="sql-tool-card__hint">Showing first {MEMORY_PREVIEW_CHARS} characters.</p>
      ) : null}
    </div>
  );
}

function ToolCardHeader({ title, status }: { title: string; status: string }) {
  return (
    <div className="sql-tool-card__header">
      <span className="sql-tool-card__badge sql-tool-card__badge--wren">{title}</span>
      <span className="sql-tool-card__status-pill">{formatStatus(status)}</span>
    </div>
  );
}

function formatStatus(status: string): string {
  const s = status.toLowerCase();
  if (s.includes("complete")) return "done";
  if (s.includes("execut")) return "running";
  return status;
}
