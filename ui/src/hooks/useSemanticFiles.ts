import { useCallback, useEffect, useState } from "react";

import { API_URL } from "../config";
import type {
  SemanticFileResponse,
  SemanticFileSaveResponse,
  SemanticTreeResponse,
  SemanticValidateResponse,
} from "../types/semanticEditor";

export function useSemanticFiles() {
  const [tree, setTree] = useState<SemanticTreeResponse | null>(null);
  const [treeLoading, setTreeLoading] = useState(true);
  const [treeError, setTreeError] = useState<string | null>(null);

  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [savedContent, setSavedContent] = useState("");
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const [validating, setValidating] = useState(false);
  const [validateResult, setValidateResult] = useState<SemanticValidateResponse | null>(
    null,
  );

  const isDirty = selectedPath !== null && content !== savedContent;

  const loadTree = useCallback(async () => {
    setTreeLoading(true);
    setTreeError(null);
    try {
      const res = await fetch(`${API_URL}/api/semantic/tree`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`,
        );
      }
      setTree((await res.json()) as SemanticTreeResponse);
    } catch (e) {
      setTree(null);
      setTreeError(e instanceof Error ? e.message : "Failed to load file tree");
    } finally {
      setTreeLoading(false);
    }
  }, []);

  const loadFile = useCallback(async (path: string) => {
    setFileLoading(true);
    setFileError(null);
    setSaveStatus(null);
    try {
      const params = new URLSearchParams({ path });
      const res = await fetch(`${API_URL}/api/semantic/file?${params}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`,
        );
      }
      const json = (await res.json()) as SemanticFileResponse;
      setSelectedPath(json.path);
      setContent(json.content);
      setSavedContent(json.content);
    } catch (e) {
      setFileError(e instanceof Error ? e.message : "Failed to load file");
    } finally {
      setFileLoading(false);
    }
  }, []);

  const selectPath = useCallback(
    (path: string) => {
      if (isDirty && !window.confirm("Discard unsaved changes?")) return;
      void loadFile(path);
    },
    [isDirty, loadFile],
  );

  const saveFile = useCallback(async () => {
    if (!selectedPath) return;
    setSaveStatus(null);
    setFileError(null);
    try {
      const params = new URLSearchParams({ path: selectedPath });
      const res = await fetch(`${API_URL}/api/semantic/file?${params}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`,
        );
      }
      const json = (await res.json()) as SemanticFileSaveResponse;
      setSavedContent(content);
      setSaveStatus(`Saved ${json.path} (${json.size} bytes)`);
      void loadTree();
    } catch (e) {
      setFileError(e instanceof Error ? e.message : "Failed to save file");
    }
  }, [selectedPath, content, loadTree]);

  const validate = useCallback(async () => {
    setValidating(true);
    setValidateResult(null);
    try {
      const res = await fetch(`${API_URL}/api/semantic/validate`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setValidateResult((await res.json()) as SemanticValidateResponse);
    } catch (e) {
      setValidateResult({
        ok: false,
        exit_code: null,
        stdout: "",
        stderr: "",
        message: e instanceof Error ? e.message : "Validate request failed",
      });
    } finally {
      setValidating(false);
    }
  }, []);

  useEffect(() => {
    void loadTree();
  }, [loadTree]);

  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!isDirty) return;
      e.preventDefault();
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [isDirty]);

  return {
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
  };
}
