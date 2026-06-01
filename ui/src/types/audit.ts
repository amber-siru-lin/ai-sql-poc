export type AuditSqlExecution = {
  tool: string;
  sql: string | null;
  result_fingerprint: string | null;
  result_preview: string | null;
  error: string | null;
};

export type AuditLogEntry = {
  timestamp: string;
  source: string;
  thread_id: string;
  run_id: string;
  semantic_layer: string;
  question: string | null;
  sql_executions: AuditSqlExecution[];
  status: string;
  duration_ms: number;
  error: string | null;
  _meta?: { file: string; line: number };
};

import type { AuditConfig } from "../config";

export type AuditLogsResponse = {
  audit: AuditConfig;
  dates: string[];
  entries: AuditLogEntry[];
};

export type AuditSession = {
  thread_id: string;
  title: string;
  first_timestamp: string;
  last_timestamp: string;
  run_count: number;
  semantic_layer: string | null;
  last_status: string | null;
};

export type AuditSessionsResponse = {
  audit: AuditLogsResponse["audit"];
  sessions: AuditSession[];
};
