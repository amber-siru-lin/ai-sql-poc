import type { SemanticLayerMode } from "../config";
import { useSemanticConsumers } from "../hooks/useSemanticConsumers";
import type { SemanticConsumer } from "../types/semanticEditor";
import { SemanticFileEditor } from "./SemanticFileEditor";
import { SemanticPrWizard } from "./SemanticPrWizard";
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
            Consumers and editable MDL/schema files. Sidebar Semantics is{" "}
            <strong>{activeSemanticMode}</strong>.
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
          <details className="semantic-page__consumers-fold">
            <summary className="semantic-page__consumers-summary">Consumers</summary>
            <div className="semantic-page__grid">
              {data.consumers.map((consumer) => (
                <ConsumerCard
                  key={consumer.id}
                  consumer={consumer}
                  highlighted={consumer.mode === activeSemanticMode}
                  onOpenFile={(path) => {
                    const el = document.getElementById("semantic-file-editor");
                    el?.scrollIntoView({ behavior: "smooth" });
                    window.dispatchEvent(
                      new CustomEvent("semantic-editor-open", { detail: { path } }),
                    );
                  }}
                />
              ))}
            </div>
          </details>

          <div id="semantic-file-editor">
            <SemanticFileEditor />
            <SemanticPrWizard />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ConsumerCard({
  consumer,
  highlighted,
  onOpenFile,
}: {
  consumer: SemanticConsumer;
  highlighted: boolean;
  onOpenFile: (path: string) => void;
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
            {p.exists ? (
              <button
                type="button"
                className="semantic-card__path-link"
                onClick={() => onOpenFile(p.path)}
              >
                <code>{p.path}</code>
              </button>
            ) : (
              <code>{p.path}</code>
            )}
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
