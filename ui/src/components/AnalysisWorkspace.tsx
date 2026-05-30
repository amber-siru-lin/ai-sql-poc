import { PlaceholderPanel } from "./PlaceholderPanel";
import { SAMPLE_QUESTIONS } from "../config";
import "./AnalysisWorkspace.css";

export function AnalysisWorkspace() {
  return (
    <div className="analysis-workspace">
      <div className="analysis-workspace__intro">
        <p>
          Ask questions about the <strong>TPCH_SF1</strong> sample dataset in plain
          English. Use the chat panel on the right — the agent will look up schema,
          write SQL, and run it on Snowflake.
        </p>
        <div className="analysis-workspace__samples">
          <span className="analysis-workspace__samples-label">Try:</span>
          {SAMPLE_QUESTIONS.map((q) => (
            <code key={q} className="sample-chip">
              {q}
            </code>
          ))}
        </div>
      </div>

      <div className="analysis-workspace__grid">
        <PlaceholderPanel
          title="SQL preview"
          hint="Final SELECT from the agent will render here with syntax highlighting."
        />
        <PlaceholderPanel
          title="Results table"
          hint="Tabular query output will appear here after execute_snowflake_sql runs."
        />
        <PlaceholderPanel
          title="Agent steps"
          badge="Phase 3.3"
          hint="Tool call timeline (schema lookup, SQL, retries) — like CLI --verbose."
        />
        <PlaceholderPanel
          title="Session context"
          badge="Phase 3.4"
          hint="Follow-up memory controls and conversation reset."
        />
      </div>
    </div>
  );
}
