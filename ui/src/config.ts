export const API_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/** CopilotKit runtime sync only — not used for agent chat (HttpAgent uses API_URL). */
export const COPILOT_RUNTIME_URL =
  import.meta.env.VITE_COPILOT_RUNTIME_URL?.replace(/\/$/, "") ??
  `${API_URL}/copilotkit`;

export const AGENT_ID = "nl2sql_assistant";

export const EDITOR_AGENT_ID = "semantic_editor";

export const EDITOR_AGENT_URL =
  import.meta.env.VITE_EDITOR_AGENT_URL?.replace(/\/$/, "") ??
  `${API_URL}/semantic-agent`;

export type SemanticLayerMode = "off" | "wren" | "cortex";

export const DEFAULT_SEMANTIC_LAYER: SemanticLayerMode = "off";

export type SemanticLayerStatus = {
  default: SemanticLayerMode;
  modes: SemanticLayerMode[];
  wren_ready: boolean;
  wren_message: string;
  cortex_ready: boolean;
  cortex_message: string;
};

export type AuditS3Status = "ok" | "error" | "not_configured";

export type AuditConfig = {
  destination: "s3" | "local" | "both";
  s3_bucket: string | null;
  s3_prefix: string;
  local_dir: string | null;
  enabled: boolean;
  s3_status?: AuditS3Status;
  s3_message?: string;
};

export type PostgresDockerStatus = {
  status: "connected" | "disconnected" | "not_configured";
  message: string;
  configured: boolean;
  backend: string;
  container: string | null;
  docker_available: boolean;
};

export type ApiStatusResponse = {
  status: string;
  agent: string;
  dataset: string;
  semantic_layer: SemanticLayerStatus;
  audit?: AuditConfig;
  postgres?: PostgresDockerStatus;
  sessions?: {
    backend: string;
    available: boolean;
  };
};

export type AppView = "chat" | "audit" | "semantic";

export const SAMPLE_QUESTIONS = [
  "What is the total amount of all orders?",
  "Show revenue by customer market segment",
  "Who are the top 5 customers by order value?",
] as const;
