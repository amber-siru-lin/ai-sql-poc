import { AssistantMessage as CopilotAssistantMessage } from "@copilotkit/react-ui";
import type { AssistantMessageProps } from "@copilotkit/react-ui";

import { chatMarkdownTagRenderers } from "./chatMarkdownRenderers";

export function AssistantMessage(props: AssistantMessageProps) {
  return (
    <CopilotAssistantMessage
      {...props}
      markdownTagRenderers={{
        ...chatMarkdownTagRenderers,
        ...props.markdownTagRenderers,
      }}
    />
  );
}
