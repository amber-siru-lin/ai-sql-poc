import { useEffect, useMemo, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

import { AppShell } from "./components/AppShell";
import { CopilotToolRenderers } from "./components/CopilotToolRenderers";
import {
  AGENT_ID,
  API_URL,
  COPILOT_RUNTIME_URL,
  type ApiStatusResponse,
} from "./config";
import { useSemanticLayerMode } from "./hooks/useSemanticLayerMode";
import { createSemanticHttpAgent } from "./lib/httpAgent";

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
      showDevConsole={false}
      enableInspector={false}
    >
      <CopilotToolRenderers />
      <AppShell
        apiStatus={apiStatus}
        semanticLayerMode={semanticLayerMode}
        semanticStatus={semanticStatus}
        onSemanticLayerChange={setSemanticLayerMode}
        chatInstructions={CHAT_INSTRUCTIONS}
      />
    </CopilotKit>
  );
}
