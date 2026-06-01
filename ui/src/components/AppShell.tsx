import { CopilotChat } from "@copilotkit/react-ui";

import type { SemanticLayerMode, SemanticLayerStatus } from "../config";
import { ContextSidebar } from "./ContextSidebar";
import { LeftSidebar } from "./LeftSidebar";
import "./AppShell.css";

const CHAT_LABELS = {
  title: "SQL Assistant",
  initial: "Ask a question about TPCH_SF1…",
} as const;

type Props = {
  apiStatus: string;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
  chatInstructions: string;
};

export function AppShell({
  apiStatus,
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
  chatInstructions,
}: Props) {
  return (
    <div className="app-layout">
      <LeftSidebar
        apiStatus={apiStatus}
        semanticLayerMode={semanticLayerMode}
        semanticStatus={semanticStatus}
        onSemanticLayerChange={onSemanticLayerChange}
      />

      <main className="app-layout__main">
        <div className="app-chat-pane">
          <CopilotChat
            className="app-chat"
            instructions={chatInstructions}
            labels={CHAT_LABELS}
          />
        </div>
      </main>

      <ContextSidebar semanticLayerMode={semanticLayerMode} />
    </div>
  );
}
