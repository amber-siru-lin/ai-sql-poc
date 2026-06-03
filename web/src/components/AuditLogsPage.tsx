import { useCallback, useEffect, useMemo, useState } from "react";

import { API_URL } from "../config";
import type { AuditLogEntry, AuditLogsResponse } from "../types/audit";
import "./AuditLogsPage.css";

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function sqlStepSummary(entry: AuditLogEntry): string {
  const n = entry.sql_executions?.length ?? 0;
  const errors = entry.sql_executions?.filter((s) => s.error).length ?? 0;
  if (n === 0) return "No SQL tools";
  if (errors > 0) return `${n} SQL step${n === 1 ? "" : "s"} · ${errors} error${errors === 1 ? "" : "s"}`;
  return `${n} SQL step${n === 1 ? "" : "s"}`;
}

const SOURCE_FILTER_OPTIONS = [
  { value: "", label: "All sources" },
  { value: "api", label: "Chat (api)" },
  { value: "semantic_editor", label: "Editor AI" },
  { value: "cli", label: "CLI" },
] as const;

type Props = {
  filterThreadId?: string;
};

export function AuditLogsPage({ filterThreadId }: Props) {
  const [data, setData] = useState<AuditLogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedSource, setSelectedSource] = useState<string>("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: "100" });
      if (selectedDate) params.set("date", selectedDate);
      if (filterThreadId) params.set("thread_id", filterThreadId);
      if (selectedSource) params.set("source", selectedSource);
      const res = await fetch(`${API_URL}/api/audit/logs?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as AuditLogsResponse;
      setData(json);
      if (!selectedDate && json.dates[0]) {
        setSelectedDate("");
      }
      setSelectedRunId((prev) => {
        if (prev && json.entries.some((e) => e.run_id === prev)) return prev;
        return json.entries[0]?.run_id ?? null;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit logs");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedDate, selectedSource, filterThreadId]);

  useEffect(() => {
    void load();
  }, [load]);

  const selected = useMemo(
    () => data?.entries.find((e) => e.run_id === selectedRunId) ?? null,
    [data, selectedRunId],
  );

  return (
    <div className="audit-page">
      <header className="audit-page__header">
        <div>
          <h1 className="audit-page__title">Query audit log</h1>
          <p className="audit-page__subtitle">
            {data?.audit.s3_bucket
              ? `S3 · ${data.audit.s3_bucket}/${data.audit.s3_prefix}`
              : "S3 audit bucket not configured"}
          </p>
        </div>
        <div className="audit-page__actions">
          <label className="audit-page__filter">
            <span>Date</span>
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              aria-label="Filter by date"
            >
              <option value="">All dates</option>
              {(data?.dates ?? []).map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
          <label className="audit-page__filter">
            <span>Source</span>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              aria-label="Filter by source"
            >
              {SOURCE_FILTER_OPTIONS.map((option) => (
                <option key={option.value || "all"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="audit-page__btn" onClick={() => void load()}>
            Refresh
          </button>
        </div>
      </header>

      {filterThreadId || selectedSource ? (
        <p className="audit-page__filter-hint">
          {filterThreadId ? (
            <>
              Showing runs for thread <code>{filterThreadId.slice(0, 8)}…</code>
              {selectedSource ? " · " : null}
            </>
          ) : null}
          {selectedSource ? (
            <>
              source{" "}
              <code>
                {SOURCE_FILTER_OPTIONS.find((o) => o.value === selectedSource)?.label ??
                  selectedSource}
              </code>
            </>
          ) : null}
        </p>
      ) : null}

      {loading ? <p className="audit-page__message">Loading…</p> : null}
      {error ? (
        <p className="audit-page__message audit-page__message--error">{error}</p>
      ) : null}

      {!loading && !error && data && data.entries.length === 0 ? (
        <p className="audit-page__message">
          No audit entries match these filters. Runs appear here after chat or editor
          agent requests when the audit bucket is configured.
        </p>
      ) : null}

      {!loading && !error && data && data.entries.length > 0 ? (
        <div className="audit-page__split">
          <ul className="audit-list" aria-label="Audit runs">
            {data.entries.map((entry) => (
              <li key={entry.run_id}>
                <button
                  type="button"
                  className={`audit-list__item${entry.run_id === selectedRunId ? " audit-list__item--active" : ""}`}
                  onClick={() => setSelectedRunId(entry.run_id)}
                >
                  <span className="audit-list__row">
                    <span
                      className={`audit-badge audit-badge--${entry.status === "ok" ? "ok" : "err"}`}
                    >
                      {entry.status}
                    </span>
                    <span className="audit-list__time">{formatTime(entry.timestamp)}</span>
                  </span>
                  <span className="audit-list__question">
                    {entry.question || "(no question captured)"}
                  </span>
                  <span className="audit-list__meta">
                    {entry.source} · {entry.semantic_layer} · {formatDuration(entry.duration_ms)} ·{" "}
                    {sqlStepSummary(entry)}
                  </span>
                </button>
              </li>
            ))}
          </ul>

          <article className="audit-detail" aria-label="Run detail">
            {selected ? (
              <>
                <h2 className="audit-detail__question">{selected.question}</h2>
                {selected.assistant_reply ? (
                  <div className="audit-detail__reply">{selected.assistant_reply}</div>
                ) : null}
                <dl className="audit-detail__meta">
                  <div>
                    <dt>Time</dt>
                    <dd>{formatTime(selected.timestamp)}</dd>
                  </div>
                  <div>
                    <dt>Duration</dt>
                    <dd>{formatDuration(selected.duration_ms)}</dd>
                  </div>
                  <div>
                    <dt>Source</dt>
                    <dd>{selected.source}</dd>
                  </div>
                  <div>
                    <dt>Semantic layer</dt>
                    <dd>{selected.semantic_layer}</dd>
                  </div>
                  <div>
                    <dt>Thread</dt>
                    <dd>
                      <code className="audit-detail__code">{selected.thread_id}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>Run ID</dt>
                    <dd>
                      <code className="audit-detail__code">{selected.run_id}</code>
                    </dd>
                  </div>
                </dl>

                {selected.error ? (
                  <pre className="audit-detail__error">{selected.error}</pre>
                ) : null}

                <h3 className="audit-detail__section-title">SQL executions</h3>
                {selected.sql_executions.length === 0 ? (
                  <p className="audit-detail__empty">No SQL tool calls recorded.</p>
                ) : (
                  <ol className="audit-steps">
                    {selected.sql_executions.map((step, i) => (
                      <li key={`${selected.run_id}-${i}`} className="audit-step">
                        <div className="audit-step__head">
                          <span className="audit-step__tool">{step.tool}</span>
                          {step.error ? (
                            <span className="audit-badge audit-badge--err">error</span>
                          ) : step.result_fingerprint ? (
                            <span className="audit-badge audit-badge--ok">ok</span>
                          ) : null}
                        </div>
                        {step.sql ? (
                          <pre className="audit-step__sql">{step.sql}</pre>
                        ) : null}
                        {step.error ? (
                          <pre className="audit-step__error">{step.error}</pre>
                        ) : null}
                        {step.result_preview && !step.error ? (
                          <details className="audit-step__preview">
                            <summary>Result preview</summary>
                            <pre>{step.result_preview}</pre>
                          </details>
                        ) : null}
                        {step.result_fingerprint ? (
                          <p className="audit-step__hash">
                            fingerprint <code>{step.result_fingerprint.slice(0, 16)}…</code>
                          </p>
                        ) : null}
                      </li>
                    ))}
                  </ol>
                )}
              </>
            ) : (
              <p className="audit-detail__empty">Select a run from the list.</p>
            )}
          </article>
        </div>
      ) : null}
    </div>
  );
}
