import { PlaceholderPanel } from "./PlaceholderPanel";
import { SAMPLE_QUESTIONS, type SemanticLayerMode } from "../config";
import "./AnalysisWorkspace.css";

const MODE_HINT: Record<SemanticLayerMode, string> = {
  off: "Markdown schema + raw Snowflake SQL (baseline).",
  wren: "Wren MDL semantic layer — use Wren tools in chat (requires wren context build).",
  cortex: "Cortex Analyst placeholder — switch to Off or Wren for live queries.",
};

type Props = {
  semanticLayerMode: SemanticLayerMode;
};

export function AnalysisWorkspace({ semanticLayerMode }: Props) {
  return (
    <div className="analysis-workspace">
      <div className="analysis-workspace__intro">
        <p>
          Ask questions about the <strong>TPCH_SF1</strong> sample dataset in plain
          English. Use the chat panel on the right — the agent will look up schema,
          write SQL, and run it on Snowflake.
        </p>
        <p className="analysis-workspace__mode-hint">
          <strong>Semantic layer:</strong> {semanticLayerMode} — {MODE_HINT[semanticLayerMode]}
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
          title="Results & charts"
          badge="In chat"
          hint="After each query, the SQL Assistant shows a table and bar chart (recharts) when the result has a category and a numeric column."
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
