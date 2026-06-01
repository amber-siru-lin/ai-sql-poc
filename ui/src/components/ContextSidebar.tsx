import { useCopilotChatHeadless_c } from "@copilotkit/react-core";

import { SAMPLE_QUESTIONS, type SemanticLayerMode } from "../config";
import { SessionPanel } from "./SessionPanel";
import "./ContextSidebar.css";

const MODE_HINT: Record<SemanticLayerMode, string> = {
  off: "Markdown schema + raw Snowflake SQL (baseline).",
  wren: "Wren MDL — use Wren tools in chat (requires wren context build).",
  cortex: "Cortex Analyst placeholder — use Off or Wren for live queries.",
};

type Props = {
  semanticLayerMode: SemanticLayerMode;
  threadId: string;
  onThreadIdChange: (nextId: string) => void;
  onOpenAuditForThread?: () => void;
};

export function ContextSidebar({
  semanticLayerMode,
  threadId,
  onThreadIdChange,
  onOpenAuditForThread,
}: Props) {
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

      <section className="context-sidebar__section">
        <SessionPanel
          semanticLayerMode={semanticLayerMode}
          threadId={threadId}
          onThreadIdChange={onThreadIdChange}
          onViewAuditLogs={onOpenAuditForThread}
        />
      </section>
    </aside>
  );
}
