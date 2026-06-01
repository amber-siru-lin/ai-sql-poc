export const SESSION_STORAGE_KEY = "ai-sql-poc-thread-id";

export function loadStoredThreadId(): string {
  const stored = localStorage.getItem(SESSION_STORAGE_KEY);
  if (stored && stored.length > 0) return stored;
  return crypto.randomUUID();
}
