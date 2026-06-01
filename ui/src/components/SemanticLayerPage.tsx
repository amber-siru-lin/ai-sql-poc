import type { SemanticLayerMode } from "../config";
import { useSemanticConsumers } from "../hooks/useSemanticConsumers";
import type { SemanticConsumer } from "../types/semanticEditor";
import "./SemanticLayerPage.css";

function modeLabel(mode: SemanticConsumer["mode"]): string {
  if (mode === "all") return "all modes";
  return mode;
}

type Props = {
  activeSemanticMode: SemanticLayerMode;
};

export function SemanticLayerPage({ activeSemanticMode }: Props) {
  const { data, loading, error, refresh } = useSemanticConsumers();

  return (
    <div className="semantic-page">
      <header className="semantic-page__header">
        <div>
          <h1 className="semantic-page__title">Semantic layer</h1>
          <p className="semantic-page__subtitle">
            Who reads which files in this repo. File editing and PR workflow are
            planned in{" "}
            <code>docs/plans/2026-06-01-006-feat-semantic-layer-editor-plan.md</code>.
            Sidebar Semantics is currently <strong>{activeSemanticMode}</strong>.
          </p>
        </div>
        <button type="button" className="semantic-page__btn" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>

      {loading ? (
        <p className="semantic-page__message">Loading consumers…</p>
      ) : null}
      {error ? (
        <p className="semantic-page__message semantic-page__message--error">{error}</p>
      ) : null}

      {data ? (
        <div className="semantic-page__scroll">
          <div className="semantic-page__grid">
            {data.consumers.map((consumer) => (
              <ConsumerCard
                key={consumer.id}
                consumer={consumer}
                highlighted={consumer.mode === activeSemanticMode}
              />
            ))}
          </div>
          <p className="semantic-page__footer">
            Repo root: <code>{data.repo_root}</code>
          </p>
        </div>
      ) : null}
    </div>
  );
}

function ConsumerCard({
  consumer,
  highlighted,
}: {
  consumer: SemanticConsumer;
  highlighted: boolean;
}) {
  const badgeClass = consumer.ready
    ? "semantic-card__badge semantic-card__badge--ok"
    : "semantic-card__badge semantic-card__badge--warn";

  return (
    <article
      className="semantic-card"
      style={
        highlighted
          ? { borderColor: "var(--copilot-kit-primary-color, #3794ff)" }
          : undefined
      }
    >
      <div className="semantic-card__head">
        <div>
          <h2 className="semantic-card__title">{consumer.name}</h2>
          <p className="semantic-card__mode">{modeLabel(consumer.mode)}</p>
        </div>
        <span className={badgeClass}>{consumer.ready ? "ready" : "not ready"}</span>
      </div>
      <p className="semantic-card__desc">{consumer.description}</p>
      {!consumer.ready && consumer.ready_message ? (
        <p className="semantic-card__ready-msg">{consumer.ready_message}</p>
      ) : null}

      <p className="semantic-card__section-title">Paths</p>
      <ul className="semantic-card__paths">
        {consumer.paths.map((p) => (
          <li
            key={p.path}
            className={`semantic-card__path${p.exists ? "" : " semantic-card__path--missing"}`}
          >
            <span className="semantic-card__path-role">{p.role}</span>
            <span className="semantic-card__path-dot" aria-hidden>
              {p.exists ? "●" : "○"}
            </span>
            <code>{p.path}</code>
          </li>
        ))}
      </ul>
      {consumer.build_artifact ? (
        <p className="semantic-card__ready-msg">
          Build artifact: <code>{consumer.build_artifact}</code> (local only)
        </p>
      ) : null}

      {consumer.tools.length > 0 ? (
        <>
          <p className="semantic-card__section-title">Agent tools</p>
          <p className="semantic-card__tools">{consumer.tools.join(", ")}</p>
        </>
      ) : null}
    </article>
  );
}
