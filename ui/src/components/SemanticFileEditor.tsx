import { useEffect } from "react";

import { useSemanticFiles } from "../hooks/useSemanticFiles";
import "./SemanticFileEditor.css";

export function SemanticFileEditor() {
  const {
    tree,
    treeLoading,
    treeError,
    loadTree,
    selectedPath,
    content,
    setContent,
    isDirty,
    fileLoading,
    fileError,
    saveStatus,
    selectPath,
    saveFile,
    validating,
    validateResult,
    validate,
  } = useSemanticFiles();

  useEffect(() => {
    const handler = (e: Event) => {
      const path = (e as CustomEvent<{ path: string }>).detail?.path;
      if (path) selectPath(path);
    };
    window.addEventListener("semantic-editor-open", handler);
    return () => window.removeEventListener("semantic-editor-open", handler);
  }, [selectPath]);

  const validateLog = [validateResult?.stdout, validateResult?.stderr]
    .filter(Boolean)
    .join("\n")
    .trim();

  return (
    <section className="semantic-editor" aria-label="Semantic file editor">
      <div className="semantic-editor__toolbar">
        <h2 className="semantic-editor__toolbar-title">Edit files</h2>
        {isDirty ? <span className="semantic-editor__dirty">Unsaved changes</span> : null}
        <button
          type="button"
          className="semantic-editor__btn"
          onClick={() => void loadTree()}
          disabled={treeLoading}
        >
          Reload tree
        </button>
        <button
          type="button"
          className="semantic-editor__btn semantic-editor__btn--primary"
          onClick={() => void saveFile()}
          disabled={!selectedPath || !isDirty || fileLoading}
        >
          Save
        </button>
        <button
          type="button"
          className="semantic-editor__btn"
          onClick={() => void validate()}
          disabled={validating}
        >
          {validating ? "Validating…" : "Validate (Wren)"}
        </button>
      </div>

      {selectedPath ? (
        <p className="semantic-editor__path">{selectedPath}</p>
      ) : (
        <p className="semantic-editor__path">Select a file to edit</p>
      )}

      <div className="semantic-editor__body">
        <ul className="semantic-editor__tree" aria-label="Editable files">
          {treeLoading ? (
            <li className="semantic-editor__tree-item">
              <span className="semantic-editor__tree-btn">Loading…</span>
            </li>
          ) : null}
          {treeError ? (
            <li className="semantic-editor__tree-item">
              <span className="semantic-editor__tree-btn">{treeError}</span>
            </li>
          ) : null}
          {tree?.files.map((f) => (
            <li key={f.path} className="semantic-editor__tree-item">
              <button
                type="button"
                className={`semantic-editor__tree-btn${
                  selectedPath === f.path ? " semantic-editor__tree-btn--active" : ""
                }`}
                onClick={() => selectPath(f.path)}
                title={f.path}
              >
                {f.path.replace(/^wren\/tpch\//, "").replace(/^schema\//, "schema/")}
              </button>
            </li>
          ))}
        </ul>

        <div className="semantic-editor__main">
          <textarea
            className="semantic-editor__textarea"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={!selectedPath || fileLoading}
            spellCheck={false}
            aria-label="File content"
            placeholder="Select a file from the list"
          />
          {fileError ? (
            <p className="semantic-editor__status semantic-editor__status--error">
              {fileError}
            </p>
          ) : null}
          {saveStatus ? (
            <p className="semantic-editor__status semantic-editor__status--ok">{saveStatus}</p>
          ) : null}
        </div>
      </div>

      {validateResult ? (
        <div
          className={`semantic-editor__validate${
            validateResult.ok
              ? " semantic-editor__validate--ok"
              : " semantic-editor__validate--fail"
          }`}
        >
          <p
            className={`semantic-editor__status${
              validateResult.ok
                ? " semantic-editor__status--ok"
                : " semantic-editor__status--error"
            }`}
          >
            {validateResult.message}
            {validateResult.exit_code !== null
              ? ` (exit ${validateResult.exit_code})`
              : ""}
          </p>
          {validateLog ? <pre>{validateLog}</pre> : null}
        </div>
      ) : null}
    </section>
  );
}
