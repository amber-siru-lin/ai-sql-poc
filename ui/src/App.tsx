import { useEffect, useMemo, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

import { AnalysisWorkspace } from "./components/AnalysisWorkspace";
import { CopilotToolRenderers } from "./components/CopilotToolRenderers";
import { SemanticLayerToggle } from "./components/SemanticLayerToggle";
import {
  AGENT_ID,
  API_URL,
  COPILOT_RUNTIME_URL,
  type ApiStatusResponse,
} from "./config";
import { useSemanticLayerMode } from "./hooks/useSemanticLayerMode";
import { createSemanticHttpAgent } from "./lib/httpAgent";
import "./App.css";

const CHAT_INSTRUCTIONS = `You are helping a business user explore the Snowflake TPCH_SF1 dataset.
Use the active semantic layer mode (Off, Wren, or Cortex) as described in your system prompt.
Always explain the answer in plain English and show the final SQL.`;

export default function App() {
  const [apiStatus, setApiStatus] = useState<string>("checking…");
  const [semanticStatus, setSemanticStatus] =
    useState<ApiStatusResponse["semantic_layer"] | null>(null);
  const { mode: semanticLayerMode, setMode: setSemanticLayerMode } =
    useSemanticLayerMode(semanticStatus);

  useEffect(() => {
    fetch(`${API_URL}/api/status`)
      .then((r) => r.json())
      .then((data: ApiStatusResponse) => {
        setApiStatus(data.status === "ok" ? "connected" : "unknown");
        setSemanticStatus(data.semantic_layer);
      })
      .catch(() => {
        setApiStatus("offline — start the API on port 8000");
        setSemanticStatus(null);
      });
  }, []);

  const agents = useMemo(
    () => ({
      [AGENT_ID]: createSemanticHttpAgent(semanticLayerMode),
    }),
    [semanticLayerMode],
  );

  return (
    <CopilotKit
      key={semanticLayerMode}
      runtimeUrl={COPILOT_RUNTIME_URL}
      agents__unsafe_dev_only={agents as never}
      agent={AGENT_ID}
    >
      <CopilotSidebar
        defaultOpen
        clickOutsideToClose={false}
        instructions={CHAT_INSTRUCTIONS}
        labels={{
          title: "SQL Assistant",
          initial: "Ask a question about TPCH_SF1…",
        }}
      >
        <CopilotToolRenderers />
        <div className="app-shell">
          <header className="app-header">
            <div>
              <p className="app-header__eyebrow">AI SQL POC · Phase 3</p>
              <h1>Natural language → Snowflake</h1>
            </div>
            <div className="app-header__meta">
              <SemanticLayerToggle
                mode={semanticLayerMode}
                status={semanticStatus}
                onChange={setSemanticLayerMode}
              />
              <span
                className={`status-pill status-pill--${apiStatus === "connected" ? "ok" : "warn"}`}
              >
                API {apiStatus}
              </span>
              <span className="status-pill">Nova Pro · TPCH_SF1</span>
            </div>
          </header>

          <main className="app-main">
            <AnalysisWorkspace semanticLayerMode={semanticLayerMode} />
          </main>
        </div>
      </CopilotSidebar>
    </CopilotKit>
  );
}
