import {
  buildChartSeries,
  parseSnowflakeToolResult,
  type SnowflakeQueryResult,
} from "../utils/parseSnowflakeToolResult";
import { isWrenToolError, parseWrenJsonResult } from "../utils/parseWrenToolResult";
import { SqlResultChart } from "./SqlResultChart";
import "./SqlToolResultCard.css";

export type QueryToolVariant = "snowflake" | "wren";

type SqlToolResultCardProps = {
  sql?: string;
  resultText?: string;
  status: string;
  variant?: QueryToolVariant;
};

export function SqlToolResultCard({
  sql,
  resultText,
  status,
  variant = "snowflake",
}: SqlToolResultCardProps) {
  const loading = !String(status).toLowerCase().includes("complete");
  const isWren = variant === "wren";
  const title = isWren ? "Wren · run SQL" : "Snowflake · run SQL";
  const loadingMessage = isWren ? "Running SQL through Wren MDL…" : "Running query on Snowflake…";

  if (loading) {
    return (
      <div
        className={`sql-tool-card sql-tool-card--loading${isWren ? " sql-tool-card--wren" : " sql-tool-card--snowflake"}`}
      >
        <ToolCardHeader title={title} status={status} snowflake={!isWren} />
        {sql ? <pre className="sql-tool-card__sql">{sql}</pre> : null}
        <span className="sql-tool-card__status-text">{loadingMessage}</span>
      </div>
    );
  }

  if (!resultText) {
    return (
      <div className={`sql-tool-card${isWren ? " sql-tool-card--wren" : ""}`}>
        <ToolCardHeader title={title} status={status} snowflake={!isWren} />
        <p className="sql-tool-card__empty">No result returned.</p>
      </div>
    );
  }

  if (isToolError(resultText, variant)) {
    return (
      <div
        className={`sql-tool-card sql-tool-card--error${isWren ? " sql-tool-card--wren" : ""}`}
      >
        <ToolCardHeader title={title} status={status} snowflake={!isWren} />
        {sql ? <pre className="sql-tool-card__sql">{sql}</pre> : null}
        <pre className="sql-tool-card__raw">{resultText}</pre>
      </div>
    );
  }

  const parsed = isWren
    ? parseWrenJsonResult(resultText)
    : parseSnowflakeToolResult(resultText);
  const chart = parsed ? buildChartSeries(parsed) : null;

  return (
    <div className={`sql-tool-card${isWren ? " sql-tool-card--wren" : " sql-tool-card--snowflake"}`}>
      <ToolCardHeader title={title} status={status} snowflake={!isWren} />
      {sql ? <pre className="sql-tool-card__sql">{sql}</pre> : null}
      {parsed ? <ResultsTable result={parsed} /> : null}
      {chart ? <SqlResultChart series={chart} /> : null}
      {!parsed ? <pre className="sql-tool-card__raw">{resultText}</pre> : null}
    </div>
  );
}

function isToolError(text: string, variant: QueryToolVariant): boolean {
  if (variant === "wren") return isWrenToolError(text);
  return text.startsWith("ERROR:") || text.startsWith("SNOWFLAKE ERROR:");
}

function ToolCardHeader({
  title,
  status,
  snowflake,
}: {
  title: string;
  status: string;
  snowflake: boolean;
}) {
  return (
    <div className="sql-tool-card__header">
      <span
        className={`sql-tool-card__badge${snowflake ? " sql-tool-card__badge--snowflake" : " sql-tool-card__badge--wren"}`}
      >
        {title}
      </span>
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

function ResultsTable({ result }: { result: SnowflakeQueryResult }) {
  return (
    <div className="sql-tool-card__table-wrap">
      <table className="sql-tool-card__table">
        <thead>
          <tr>
            {result.columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, i) => (
            <tr key={i}>
              {result.columns.map((_, j) => (
                <td key={j}>{formatCell(row[j])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  return String(value);
}
