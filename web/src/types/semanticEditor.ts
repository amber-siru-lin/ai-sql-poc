import type { SemanticLayerMode, SemanticLayerStatus } from "../config";

export type SemanticConsumerPath = {
  path: string;
  role: string;
  exists: boolean;
};

export type SemanticConsumer = {
  id: string;
  name: string;
  mode: SemanticLayerMode | "all";
  description: string;
  paths: SemanticConsumerPath[];
  tools: string[];
  ready: boolean;
  ready_message: string;
  build_artifact?: string;
};

export type SemanticConsumersResponse = {
  repo_root: string;
  semantic_layer: SemanticLayerStatus;
  consumers: SemanticConsumer[];
};

export type SemanticFileEntry = {
  path: string;
  size: number;
  modified: number;
};

export type SemanticTreeResponse = {
  roots: string[];
  files: SemanticFileEntry[];
};

export type SemanticFileResponse = {
  path: string;
  content: string;
};

export type SemanticFileSaveResponse = {
  path: string;
  saved: boolean;
  size: number;
};

export type SemanticValidateResponse = {
  ok: boolean;
  exit_code: number | null;
  stdout: string;
  stderr: string;
  message: string;
};

export type SemanticPrConfigResponse = {
  configured: boolean;
  token_present: boolean;
  repo: string;
  default_branch: string;
};

export type SemanticPrDraftResponse = {
  title: string;
  body: string;
  paths: string[];
  base_branch: string;
  branch_name: string;
  github: {
    configured: boolean;
    repo: string;
    default_branch: string;
  };
  diff_stat: string;
};

export type SemanticPrCreateRequest = {
  title: string;
  body: string;
  paths?: string[];
  base_branch?: string;
  branch_name?: string;
  audit_entry_ids?: string[];
  require_validate?: boolean;
};

export type SemanticPrCreateResponse = {
  ok: boolean;
  branch: string;
  base_branch: string;
  commit_sha: string;
  paths: string[];
  pr_number: number;
  pr_url: string;
  pr_title: string;
};
