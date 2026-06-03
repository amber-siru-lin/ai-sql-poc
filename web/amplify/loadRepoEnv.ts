import fs from 'node:fs';
import path from 'node:path';

/** Parse repo-root `.env` at synth/deploy time (never commit secrets). */
export function loadRepoEnv(repoRoot: string): Record<string, string> {
  const envPath = path.join(repoRoot, '.env');
  const out: Record<string, string> = {};
  if (!fs.existsSync(envPath)) return out;

  for (const raw of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const key = line.slice(0, line.indexOf('=')).trim();
    let value = line.slice(line.indexOf('=') + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (key) out[key] = value;
  }
  return out;
}

/** Env vars safe to pass into the sandbox Lambda (no localhost DB). */
export function lambdaRuntimeEnv(repoRoot: string): Record<string, string> {
  const e = loadRepoEnv(repoRoot);
  const out: Record<string, string> = {
    LAMBDA_APP_MODULE: 'api.main',
    AUDIT_DESTINATION: e.AUDIT_DESTINATION?.trim() || 's3',
  };

  if (e.AUDIT_S3_BUCKET?.trim()) out.AUDIT_S3_BUCKET = e.AUDIT_S3_BUCKET.trim();
  if (e.AUDIT_S3_PREFIX?.trim()) out.AUDIT_S3_PREFIX = e.AUDIT_S3_PREFIX.trim();
  if (e.BEDROCK_MODEL_ID?.trim()) out.BEDROCK_MODEL_ID = e.BEDROCK_MODEL_ID.trim();

  const db = (e.LAMBDA_DATABASE_URL || e.DATABASE_URL || '').trim();
  if (db && !/localhost|127\.0\.0\.1/i.test(db)) {
    out.DATABASE_URL = db;
  }

  return out;
}
