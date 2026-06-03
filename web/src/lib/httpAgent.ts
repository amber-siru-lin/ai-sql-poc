import { HttpAgent } from "@ag-ui/client";
import type { MutableRefObject } from "react";

import { AGENT_ID, API_URL, type SemanticLayerMode } from "../config";

/** Inject semantic layer + LangGraph thread into each AG-UI run. */
export function createSemanticHttpAgent(
  semanticLayerRef: MutableRefObject<SemanticLayerMode>,
  threadIdRef: MutableRefObject<string>,
): HttpAgent {
  const agent = new HttpAgent({
    url: API_URL,
    agentId: AGENT_ID,
    threadId: threadIdRef.current,
    fetch: async (url, requestInit) => {
      agent.threadId = threadIdRef.current;
      let init: RequestInit = requestInit ?? {};
      if (init.body && typeof init.body === "string") {
        try {
          const body = JSON.parse(init.body) as {
            threadId?: string;
            forwardedProps?: Record<string, unknown>;
          };
          body.threadId = threadIdRef.current;
          const mode = semanticLayerRef.current;
          body.forwardedProps = {
            ...body.forwardedProps,
            semanticLayer: mode,
            semantic_layer: mode,
          };
          init = { ...init, body: JSON.stringify(body) };
        } catch {
          // Non-JSON body — pass through unchanged.
        }
      }
      return fetch(url, init);
    },
  });
  return agent;
}
