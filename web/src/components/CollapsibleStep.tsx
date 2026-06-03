import type { ReactNode } from "react";
import "./AgentStep.css";

type CollapsibleStepProps = {
  title: string;
  preview?: string;
  defaultOpen?: boolean;
  children: ReactNode;
};

export function CollapsibleStep({
  title,
  preview,
  defaultOpen = false,
  children,
}: CollapsibleStepProps) {
  return (
    <details className="agent-step" open={defaultOpen}>
      <summary className="agent-step__summary">
        <span className="agent-step__title">{title}</span>
        {preview ? <span className="agent-step__preview">{preview}</span> : null}
      </summary>
      <div className="agent-step__body">{children}</div>
    </details>
  );
}

export function InlineAgentStep({ label }: { label: string }) {
  return (
    <div className="agent-step agent-step--inline" role="status">
      <span className="agent-step__pulse" aria-hidden />
      <span>{label}</span>
    </div>
  );
}
