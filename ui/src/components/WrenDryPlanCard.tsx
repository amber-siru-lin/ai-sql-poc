import { isWrenToolError } from "../utils/parseWrenToolResult";
import "./SqlToolResultCard.css";

type Props = {
  modeledSql?: string;
  planText?: string;
  status: string;
};

export function WrenDryPlanCard({ modeledSql, planText, status }: Props) {
  const loading = !String(status).toLowerCase().includes("complete");

  if (loading) {
    return (
      <div className="sql-tool-card sql-tool-card--loading sql-tool-card--wren">
        <ToolCardHeader title="Wren · dry plan" status={status} />
        {modeledSql ? <pre className="sql-tool-card__sql">{modeledSql}</pre> : null}
        <span className="sql-tool-card__status-text">Expanding through MDL…</span>
      </div>
    );
  }

  if (!planText) {
    return (
      <div className="sql-tool-card sql-tool-card--wren">
        <ToolCardHeader title="Wren · dry plan" status={status} />
        <p className="sql-tool-card__empty">No plan returned.</p>
      </div>
    );
  }

  if (isWrenToolError(planText)) {
    return (
      <div className="sql-tool-card sql-tool-card--error sql-tool-card--wren">
        <ToolCardHeader title="Wren · dry plan" status={status} />
        {modeledSql ? <pre className="sql-tool-card__sql">{modeledSql}</pre> : null}
        <pre className="sql-tool-card__raw">{planText}</pre>
      </div>
    );
  }

  return (
    <div className="sql-tool-card sql-tool-card--wren">
      <ToolCardHeader title="Wren · dry plan" status={status} />
      {modeledSql ? (
        <section className="sql-tool-card__section">
          <h4 className="sql-tool-card__section-title">Modeled SQL</h4>
          <pre className="sql-tool-card__sql">{modeledSql}</pre>
        </section>
      ) : null}
      <section className="sql-tool-card__section">
        <h4 className="sql-tool-card__section-title">Expanded SQL</h4>
        <pre className="sql-tool-card__sql sql-tool-card__sql--expanded">{planText}</pre>
      </section>
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
