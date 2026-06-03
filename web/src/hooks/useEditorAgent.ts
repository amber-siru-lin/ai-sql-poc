import { UseAgentUpdate, useAgent } from "@copilotkit/react-core/v2";

import { EDITOR_AGENT_ID } from "../config";

type Options = {
  watchMessages?: boolean;
};

export function useEditorAgent({ watchMessages = false }: Options = {}) {
  return useAgent({
    agentId: EDITOR_AGENT_ID,
    updates: watchMessages
      ? [UseAgentUpdate.OnMessagesChanged, UseAgentUpdate.OnRunStatusChanged]
      : [UseAgentUpdate.OnRunStatusChanged],
  });
}
