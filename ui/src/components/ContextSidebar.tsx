import { useCopilotKit } from "@copilotkit/react-core/v2";

import { SAMPLE_QUESTIONS, type ApiStatusResponse, type AuditConfig, type SemanticLayerMode } from "../config";
import { useSqlAgent } from "../hooks/useSqlAgent";
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
  apiStatusPayload: ApiStatusResponse | null;
  auditStatus: AuditConfig | null;
  onOpenAuditForThread?: () => void;
};

export function ContextSidebar({
  semanticLayerMode,
  threadId,
  apiStatusPayload,
  auditStatus,
  onOpenAuditForThread,
}: Props) {
  const { agent } = useSqlAgent();
  const { copilotkit } = useCopilotKit();
  const isLoading = Boolean(agent?.isRunning);
  const datasetLabel = apiStatusPayload?.dataset ?? "your dataset";

  const ask = (question: string) => {
    if (!agent || isLoading) return;
    void (async () => {
      agent.addMessage({
        id: crypto.randomUUID(),
        role: "user",
        content: question,
      });
      await copilotkit.runAgent({ agent });
    })();
  };

  return (
    <aside className="context-sidebar" aria-label="Context">
      <section className="context-sidebar__section">
        <h2 className="context-sidebar__section-title">Suggested questions</h2>
        <p className="context-sidebar__hint">
          Click to send to the assistant. Dataset: <strong>{datasetLabel}</strong>.
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
          auditStatus={auditStatus}
          onViewAuditLogs={onOpenAuditForThread}
        />
      </section>
    </aside>
  );
}
