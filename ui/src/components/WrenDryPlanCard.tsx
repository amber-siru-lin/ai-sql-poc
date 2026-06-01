import { CollapsibleStep, InlineAgentStep } from "./CollapsibleStep";
import { isWrenToolError } from "../utils/parseWrenToolResult";
import "./SqlToolResultCard.css";
import "./AgentStep.css";

type Props = {
  modeledSql?: string;
  planText?: string;
  status: string;
};

export function WrenDryPlanCard({ modeledSql, planText, status }: Props) {
  const loading = !String(status).toLowerCase().includes("complete");

  if (loading) {
    return <InlineAgentStep label="Wren · expanding SQL through MDL…" />;
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

  const preview = planText.replace(/\s+/g, " ").slice(0, 72);
  return (
    <CollapsibleStep title="Wren · dry plan" preview={preview ? `${preview}…` : "Expanded SQL"}>
      {modeledSql ? (
        <>
          <p className="sql-tool-card__section-title">Modeled SQL</p>
          <pre>{modeledSql}</pre>
        </>
      ) : null}
      <p className="sql-tool-card__section-title">Expanded SQL</p>
      <pre>{planText}</pre>
    </CollapsibleStep>
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
