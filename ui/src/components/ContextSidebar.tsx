import { useCopilotChatHeadless_c } from "@copilotkit/react-core";

import { SAMPLE_QUESTIONS, type SemanticLayerMode } from "../config";
import { PlaceholderPanel } from "./PlaceholderPanel";
import "./ContextSidebar.css";

const MODE_HINT: Record<SemanticLayerMode, string> = {
  off: "Markdown schema + raw Snowflake SQL (baseline).",
  wren: "Wren MDL — use Wren tools in chat (requires wren context build).",
  cortex: "Cortex Analyst placeholder — use Off or Wren for live queries.",
};

type Props = {
  semanticLayerMode: SemanticLayerMode;
};

export function ContextSidebar({ semanticLayerMode }: Props) {
  const { sendMessage, isLoading } = useCopilotChatHeadless_c();

  const ask = (question: string) => {
    if (isLoading) return;
    void sendMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    });
  };

  return (
    <aside className="context-sidebar" aria-label="Context">
      <section className="context-sidebar__section">
        <h2 className="context-sidebar__section-title">Suggested questions</h2>
        <p className="context-sidebar__hint">
          Click to send to the assistant. Dataset: <strong>TPCH_SF1</strong>.
        </p>
        <ul className="context-sidebar__questions">
          {SAMPLE_QUESTIONS.map((q) => (
            <li key={q}>
              <button
                type="button"
                className="context-sidebar__question-btn"
                disabled={isLoading}
                onClick={() => ask(q)}
              >
                {q}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="context-sidebar__section">
        <h2 className="context-sidebar__section-title">Semantic layer</h2>
        <p className="context-sidebar__mode">
          <span className="context-sidebar__mode-badge">{semanticLayerMode}</span>
          {MODE_HINT[semanticLayerMode]}
        </p>
      </section>

      <section className="context-sidebar__section context-sidebar__cards">
        <h2 className="context-sidebar__section-title">Workspace panels</h2>
        <PlaceholderPanel
          title="SQL preview"
          badge="Phase 3.2"
          hint="Final SELECT from the agent will render here with syntax highlighting."
        />
        <PlaceholderPanel
          title="Results & charts"
          badge="In chat"
          hint="Tables and bar charts also appear inline in the chat when results are chartable."
        />
        <PlaceholderPanel
          title="Agent steps"
          badge="Phase 3.3"
          hint="Tool call timeline (schema lookup, SQL, retries)."
        />
        <PlaceholderPanel
          title="Session context"
          badge="Phase 3.4"
          hint="Follow-up memory controls and conversation reset."
        />
      </section>
    </aside>
  );
}
