import { useEffect, useState } from "react";

import { useSemanticPr } from "../hooks/useSemanticPr";
import "./SemanticPrWizard.css";

export function SemanticPrWizard() {
  const [open, setOpen] = useState(false);
  const {
    config,
    draft,
    title,
    setTitle,
    body,
    setBody,
    branchName,
    setBranchName,
    baseBranch,
    setBaseBranch,
    loadingConfig,
    loadingDraft,
    submitting,
    error,
    result,
    loadConfig,
    loadDraft,
    submitPr,
  } = useSemanticPr();

  useEffect(() => {
    if (!open) return;
    void loadConfig();
    void loadDraft();
  }, [open, loadConfig, loadDraft]);

  return (
    <section className="semantic-pr" aria-label="Open pull request">
      <div className="semantic-pr__toolbar">
        <h2 className="semantic-pr__title">Pull request</h2>
        <button
          type="button"
          className="semantic-pr__btn"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Hide PR wizard" : "Open PR wizard"}
        </button>
        {open ? (
          <button
            type="button"
            className="semantic-pr__btn"
            onClick={() => void loadDraft()}
            disabled={loadingDraft}
          >
            {loadingDraft ? "Refreshing…" : "Refresh draft"}
          </button>
        ) : null}
      </div>

      {open ? (
        <div className="semantic-pr__panel">
          {loadingConfig ? (
            <p className="semantic-pr__hint">Loading GitHub config…</p>
          ) : config ? (
            <p className="semantic-pr__hint">
              GitHub:{" "}
              {config.configured ? (
                <>
                  <strong>{config.repo || "repo"}</strong> (token set)
                </>
              ) : (
                <>
                  not configured — set <code>GITHUB_TOKEN</code> and{" "}
                  <code>GITHUB_REPO</code> in API <code>.env</code>
                </>
              )}
            </p>
          ) : null}

          {draft ? (
            <>
              <p className="semantic-pr__paths">
                Files: {draft.paths.length ? draft.paths.join(", ") : "none"}
              </p>
              {draft.diff_stat ? (
                <pre className="semantic-pr__diff">{draft.diff_stat}</pre>
              ) : null}

              <label className="semantic-pr__field">
                <span>Title</span>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={submitting}
                />
              </label>

              <label className="semantic-pr__field">
                <span>Base branch</span>
                <input
                  type="text"
                  value={baseBranch}
                  onChange={(e) => setBaseBranch(e.target.value)}
                  disabled={submitting}
                />
              </label>

              <label className="semantic-pr__field">
                <span>Head branch</span>
                <input
                  type="text"
                  value={branchName}
                  onChange={(e) => setBranchName(e.target.value)}
                  disabled={submitting}
                />
              </label>

              <label className="semantic-pr__field semantic-pr__field--body">
                <span>Description</span>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  disabled={submitting}
                  spellCheck={false}
                />
              </label>

              <div className="semantic-pr__actions">
                <button
                  type="button"
                  className="semantic-pr__btn semantic-pr__btn--primary"
                  onClick={() => void submitPr()}
                  disabled={
                    submitting ||
                    !config?.configured ||
                    !title.trim() ||
                    !draft.paths.length
                  }
                >
                  {submitting ? "Opening PR…" : "Create pull request"}
                </button>
              </div>
            </>
          ) : loadingDraft ? (
            <p className="semantic-pr__hint">Building draft from git diff…</p>
          ) : null}

          {error ? <p className="semantic-pr__error">{error}</p> : null}

          {result ? (
            <p className="semantic-pr__success">
              Opened PR #{result.pr_number}:{" "}
              <a href={result.pr_url} target="_blank" rel="noreferrer">
                {result.pr_url}
              </a>
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
