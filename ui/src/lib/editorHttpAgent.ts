import { HttpAgent } from "@ag-ui/client";
import type { MutableRefObject } from "react";

import { EDITOR_AGENT_ID, EDITOR_AGENT_URL } from "../config";

export type EditorAgentContext = {
  path: string | null;
  content: string;
};

/** AG-UI client for the semantic layer editor agent at /semantic-agent. */
export function createEditorHttpAgent(
  editorContextRef: MutableRefObject<EditorAgentContext>,
  threadIdRef: MutableRefObject<string>,
): HttpAgent {
  const agent = new HttpAgent({
    url: EDITOR_AGENT_URL,
    agentId: EDITOR_AGENT_ID,
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
          const ctx = editorContextRef.current;
          body.forwardedProps = {
            ...body.forwardedProps,
            activeFile: ctx.path,
            active_file: ctx.path,
            activeFileContent: ctx.content,
            active_file_content: ctx.content,
          };
          init = { ...init, body: JSON.stringify(body) };
        } catch {
          // pass through
        }
      }
      return fetch(url, init);
    },
  });
  return agent;
}
