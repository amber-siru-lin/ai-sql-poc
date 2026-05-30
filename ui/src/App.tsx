import { HttpAgent } from "@ag-ui/client";
import { useEffect, useMemo, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

import { AnalysisWorkspace } from "./components/AnalysisWorkspace";
import { AGENT_ID, API_URL, COPILOT_RUNTIME_URL } from "./config";
import "./App.css";

const CHAT_INSTRUCTIONS = `You are helping a business user explore the Snowflake TPCH_SF1 dataset.
Use get_schema_summary when you need table or column names, then execute_snowflake_sql.
Always explain the answer in plain English and show the final SQL.`;

function AppShell() {
  const [apiStatus, setApiStatus] = useState<string>("checking…");

  useEffect(() => {
    fetch(`${API_URL}/api/status`)
      .then((r) => r.json())
      .then((data) => setApiStatus(data.status === "ok" ? "connected" : "unknown"))
      .catch(() => setApiStatus("offline — start the API on port 8000"));
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-header__eyebrow">AI SQL POC · Phase 3</p>
          <h1>Natural language → Snowflake</h1>
        </div>
        <div className="app-header__meta">
          <span className={`status-pill status-pill--${apiStatus === "connected" ? "ok" : "warn"}`}>
            API {apiStatus}
          </span>
          <span className="status-pill">Nova Pro · TPCH_SF1</span>
        </div>
      </header>

      <main className="app-main">
        <AnalysisWorkspace />
      </main>
    </div>
  );
}

export default function App() {
  // Direct AG-UI connection — avoids CopilotKit /info format mismatch (Python SDK returns agents[]).
  const agents = useMemo(
    () => ({
      [AGENT_ID]: new HttpAgent({
        url: API_URL,
        agentId: AGENT_ID,
        // HttpAgent calls `this.fetch(...)`; unbound global fetch throws in browsers.
        fetch: (input, init) => fetch(input, init),
      }),
    }),
    [],
  );

  return (
    <CopilotKit
      // Satisfies CopilotKit validateProps; /copilotkit stub returns empty agents so HttpAgent stays in control.
      runtimeUrl={COPILOT_RUNTIME_URL}
      agents__unsafe_dev_only={agents as never}
      agent={AGENT_ID}
      showDevConsole={import.meta.env.DEV}
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
        <AppShell />
      </CopilotSidebar>
    </CopilotKit>
  );
}
