import { useRenderToolCall } from "@copilotkit/react-core";

import { SqlToolResultCard } from "./SqlToolResultCard";
import { WrenDryPlanCard } from "./WrenDryPlanCard";
import { WrenMemoryCard } from "./WrenMemoryCard";

function toolArgString(args: unknown, key: string): string | undefined {
  if (!args || typeof args !== "object" || !(key in args)) return undefined;
  return String((args as Record<string, unknown>)[key]);
}

function toolResultString(result: unknown): string | undefined {
  if (typeof result === "string") return result;
  if (result === null || result === undefined) return undefined;
  return String(result);
}

/** Registers CopilotKit tool UI (must render inside CopilotKit provider). */
export function CopilotToolRenderers() {
  useRenderToolCall({
    name: "execute_snowflake_sql",
    render: ({ status, args, result }) => (
      <SqlToolResultCard
        variant="snowflake"
        sql={toolArgString(args, "sql")}
        resultText={toolResultString(result)}
        status={String(status)}
      />
    ),
  });

  useRenderToolCall({
    name: "wren_run_sql",
    render: ({ status, args, result }) => (
      <SqlToolResultCard
        variant="wren"
        sql={toolArgString(args, "sql")}
        resultText={toolResultString(result)}
        status={String(status)}
      />
    ),
  });

  useRenderToolCall({
    name: "wren_dry_plan",
    render: ({ status, args, result }) => (
      <WrenDryPlanCard
        modeledSql={toolArgString(args, "sql")}
        planText={toolResultString(result)}
        status={String(status)}
      />
    ),
  });

  useRenderToolCall({
    name: "wren_memory_fetch",
    render: ({ status, args, result }) => (
      <WrenMemoryCard
        question={toolArgString(args, "question")}
        memoryText={toolResultString(result)}
        status={String(status)}
      />
    ),
  });

  useRenderToolCall({
    name: "get_schema_summary",
    render: ({ status, result }) => {
      const loading = !String(status).toLowerCase().includes("complete");
      if (loading) {
        return (
          <div className="sql-tool-card sql-tool-card--loading sql-tool-card--snowflake">
            <span className="sql-tool-card__badge sql-tool-card__badge--snowflake">
              Snowflake · schema
            </span>
            <span className="sql-tool-card__status-text">Loading schema…</span>
          </div>
        );
      }
      const text = toolResultString(result) ?? "";
      return (
        <div className="sql-tool-card sql-tool-card--snowflake">
          <span className="sql-tool-card__badge sql-tool-card__badge--snowflake">
            Snowflake · schema
          </span>
          <pre className="sql-tool-card__raw">
            {text.slice(0, 1200)}
            {text.length > 1200 ? "…" : ""}
          </pre>
        </div>
      );
    },
  });

  return null;
}
