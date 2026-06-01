import type { SemanticLayerMode, SemanticLayerStatus } from "../config";
import { SemanticLayerToggle } from "./SemanticLayerToggle";
import "./LeftSidebar.css";

type Props = {
  apiStatus: string;
  semanticLayerMode: SemanticLayerMode;
  semanticStatus: SemanticLayerStatus | null;
  onSemanticLayerChange: (mode: SemanticLayerMode) => void;
};

export function LeftSidebar({
  apiStatus,
  semanticLayerMode,
  semanticStatus,
  onSemanticLayerChange,
}: Props) {
  const apiOk = apiStatus === "connected";

  return (
    <aside className="left-sidebar" aria-label="Workspace">
      <div className="left-sidebar__brand">
        <p className="left-sidebar__eyebrow">AI SQL POC</p>
        <h1 className="left-sidebar__title">TPCH Assistant</h1>
        <p className="left-sidebar__subtitle">Natural language → Snowflake</p>
      </div>

      <section className="left-sidebar__section">
        <h2 className="left-sidebar__section-title">Semantic layer</h2>
        <SemanticLayerToggle
          mode={semanticLayerMode}
          status={semanticStatus}
          onChange={onSemanticLayerChange}
        />
      </section>

      <section className="left-sidebar__section">
        <h2 className="left-sidebar__section-title">Connection</h2>
        <ul className="left-sidebar__status-list">
          <li>
            <span
              className={`status-dot status-dot--${apiOk ? "ok" : "warn"}`}
              aria-hidden
            />
            API {apiStatus}
          </li>
          <li>
            <span className="status-dot status-dot--ok" aria-hidden />
            Nova Pro · TPCH_SF1
          </li>
        </ul>
      </section>

      <section className="left-sidebar__section left-sidebar__section--grow">
        <h2 className="left-sidebar__section-title">Chat history</h2>
        <p className="left-sidebar__placeholder">
          Thread list and past sessions will live here in a later phase.
        </p>
      </section>
    </aside>
  );
}
