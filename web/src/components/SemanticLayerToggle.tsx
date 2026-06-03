import type { SemanticLayerMode, SemanticLayerStatus } from "../config";

import "./SemanticLayerToggle.css";

const OPTIONS: { value: SemanticLayerMode; label: string }[] = [
  { value: "off", label: "Off" },
  { value: "wren", label: "Wren" },
  { value: "cortex", label: "Cortex" },
];

type Props = {
  mode: SemanticLayerMode;
  status: SemanticLayerStatus | null;
  onChange: (mode: SemanticLayerMode) => void;
};

export function SemanticLayerToggle({ mode, status, onChange }: Props) {
  return (
    <div className="semantic-toggle" role="group" aria-label="Semantic layer mode">
      <span className="semantic-toggle__label">Semantics</span>
      {OPTIONS.map(({ value, label }) => {
        const disabled =
          (value === "wren" && status !== null && !status.wren_ready) ||
          (value === "cortex" && status !== null && !status.cortex_ready);
        const title =
          value === "wren" && disabled
            ? status?.wren_message ?? "Wren not ready"
            : value === "cortex"
              ? status?.cortex_message ?? "Cortex not configured yet"
              : undefined;

        return (
          <button
            key={value}
            type="button"
            className={`semantic-toggle__btn${mode === value ? " semantic-toggle__btn--active" : ""}${disabled ? " semantic-toggle__btn--disabled" : ""}`}
            aria-pressed={mode === value}
            disabled={disabled}
            title={title}
            onClick={() => onChange(value)}
          >
            {label}
          </button>
        );
      })}
      {status && !status.wren_ready ? (
        <p className="semantic-toggle__hint" title={status.wren_message}>
          Wren: {status.wren_message}
        </p>
      ) : null}
      {status && !status.cortex_ready ? (
        <p className="semantic-toggle__hint" title={status.cortex_message}>
          Cortex: {status.cortex_message}
        </p>
      ) : null}
    </div>
  );
}
