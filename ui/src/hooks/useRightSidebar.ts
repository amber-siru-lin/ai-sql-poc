const RIGHT_SIDEBAR_STORAGE_KEY = "ai-sql-poc-right-sidebar-open";

export function loadRightSidebarOpen(): boolean {
  try {
    const stored = localStorage.getItem(RIGHT_SIDEBAR_STORAGE_KEY);
    if (stored === "0" || stored === "false") return false;
    if (stored === "1" || stored === "true") return true;
  } catch {
    // ignore
  }
  return true;
}

export function saveRightSidebarOpen(open: boolean): void {
  try {
    localStorage.setItem(RIGHT_SIDEBAR_STORAGE_KEY, open ? "1" : "0");
  } catch {
    // ignore
  }
}

export { RIGHT_SIDEBAR_STORAGE_KEY };
