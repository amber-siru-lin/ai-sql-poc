import type { ReactNode } from "react";
import "./PlaceholderPanel.css";

type PlaceholderPanelProps = {
  title: string;
  badge?: string;
  children?: ReactNode;
  hint?: string;
};

/** MVP shell — replace inner content as features land. */
export function PlaceholderPanel({
  title,
  badge = "Coming soon",
  children,
  hint,
}: PlaceholderPanelProps) {
  return (
    <section className="placeholder-panel">
      <header className="placeholder-panel__header">
        <h2>{title}</h2>
        <span className="placeholder-panel__badge">{badge}</span>
      </header>
      <div className="placeholder-panel__body">
        {children ?? (
          <p className="placeholder-panel__hint">
            {hint ?? "Placeholder — wire this panel in a future iteration."}
          </p>
        )}
      </div>
    </section>
  );
}
