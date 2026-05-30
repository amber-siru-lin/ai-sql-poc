export const API_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/** CopilotKit runtime sync only — not used for agent chat (HttpAgent uses API_URL). */
export const COPILOT_RUNTIME_URL =
  import.meta.env.VITE_COPILOT_RUNTIME_URL?.replace(/\/$/, "") ??
  `${API_URL}/copilotkit`;

export const AGENT_ID = "nl2sql_assistant";

export const SAMPLE_QUESTIONS = [
  "What is the total amount of all orders?",
  "Show revenue by customer market segment",
  "Who are the top 5 customers by order value?",
] as const;
