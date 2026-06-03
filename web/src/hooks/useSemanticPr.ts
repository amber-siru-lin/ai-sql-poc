import { useCallback, useState } from "react";

import { API_URL } from "../config";
import type {
  SemanticPrConfigResponse,
  SemanticPrCreateRequest,
  SemanticPrCreateResponse,
  SemanticPrDraftResponse,
} from "../types/semanticEditor";

export function useSemanticPr() {
  const [config, setConfig] = useState<SemanticPrConfigResponse | null>(null);
  const [draft, setDraft] = useState<SemanticPrDraftResponse | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [branchName, setBranchName] = useState("");
  const [baseBranch, setBaseBranch] = useState("main");
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SemanticPrCreateResponse | null>(null);

  const loadConfig = useCallback(async () => {
    setLoadingConfig(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/semantic/pr/config`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as SemanticPrConfigResponse;
      setConfig(json);
      setBaseBranch(json.default_branch || "main");
    } catch (e) {
      setConfig(null);
      setError(e instanceof Error ? e.message : "Failed to load GitHub config");
    } finally {
      setLoadingConfig(false);
    }
  }, []);

  const loadDraft = useCallback(async (paths?: string[]) => {
    setLoadingDraft(true);
    setError(null);
    setResult(null);
    try {
      const params = new URLSearchParams();
      if (paths?.length) params.set("paths", paths.join(","));
      if (baseBranch) params.set("base_branch", baseBranch);
      const qs = params.toString();
      const res = await fetch(`${API_URL}/api/semantic/pr/draft${qs ? `?${qs}` : ""}`);
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof payload.detail === "string" ? payload.detail : `HTTP ${res.status}`,
        );
      }
      const json = payload as SemanticPrDraftResponse;
      setDraft(json);
      setTitle(json.title);
      setBody(json.body);
      setBranchName(json.branch_name);
      setBaseBranch(json.base_branch);
    } catch (e) {
      setDraft(null);
      setError(e instanceof Error ? e.message : "Failed to build PR draft");
    } finally {
      setLoadingDraft(false);
    }
  }, [baseBranch]);

  const submitPr = useCallback(async () => {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const payload: SemanticPrCreateRequest = {
        title: title.trim(),
        body,
        paths: draft?.paths,
        base_branch: baseBranch.trim() || undefined,
        branch_name: branchName.trim() || undefined,
        require_validate: true,
      };
      const res = await fetch(`${API_URL}/api/semantic/pr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`,
        );
      }
      setResult(json as SemanticPrCreateResponse);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open pull request");
    } finally {
      setSubmitting(false);
    }
  }, [title, body, draft?.paths, baseBranch, branchName]);

  return {
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
  };
}
