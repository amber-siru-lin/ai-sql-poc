import { UseAgentUpdate, useAgent } from "@copilotkit/react-core/v2";

import { AGENT_ID } from "../config";

type Options = {
  /** Re-render when the agent message list changes (persistence, restore, counts). */
  watchMessages?: boolean;
};

/** Shared HttpAgent handle — avoids duplicate useCopilotChatInternal connectAgent clears. */
export function useSqlAgent({ watchMessages = false }: Options = {}) {
  return useAgent({
    agentId: AGENT_ID,
    updates: watchMessages
      ? [UseAgentUpdate.OnMessagesChanged, UseAgentUpdate.OnRunStatusChanged]
      : [UseAgentUpdate.OnRunStatusChanged],
  });
}
