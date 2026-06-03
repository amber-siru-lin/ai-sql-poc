const EDITOR_SESSION_STORAGE_KEY = "ai-sql-poc-editor-thread-id";

export function loadEditorThreadId(): string {
  const stored = localStorage.getItem(EDITOR_SESSION_STORAGE_KEY);
  if (stored?.trim()) return stored;
  const id = crypto.randomUUID();
  localStorage.setItem(EDITOR_SESSION_STORAGE_KEY, id);
  return id;
}

export function resetEditorThreadId(): string {
  const id = crypto.randomUUID();
  localStorage.setItem(EDITOR_SESSION_STORAGE_KEY, id);
  return id;
}

export { EDITOR_SESSION_STORAGE_KEY };
