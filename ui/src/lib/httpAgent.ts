import { HttpAgent } from "@ag-ui/client";

import { AGENT_ID, API_URL, type SemanticLayerMode } from "../config";

/** Inject semantic layer mode into each AG-UI run via ``forwardedProps``. */
export function createSemanticHttpAgent(semanticLayer: SemanticLayerMode): HttpAgent {
  return new HttpAgent({
    url: API_URL,
    agentId: AGENT_ID,
    fetch: async (url, requestInit) => {
      let init: RequestInit = requestInit ?? {};
      if (init.body && typeof init.body === "string") {
        try {
          const body = JSON.parse(init.body) as {
            forwardedProps?: Record<string, unknown>;
          };
          body.forwardedProps = {
            ...body.forwardedProps,
            semanticLayer,
          };
          init = { ...init, body: JSON.stringify(body) };
        } catch {
          // Non-JSON body — pass through unchanged.
        }
      }
      return fetch(url, init);
    },
  });
}
