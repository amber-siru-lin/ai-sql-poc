import type { SnowflakeQueryResult } from "./parseSnowflakeToolResult";

/** Parse wren_run_sql output (`-o json`, one JSON object per line). */
export function parseWrenJsonResult(text: string): SnowflakeQueryResult | null {
  if (!text || isWrenToolError(text)) return null;

  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"));

  if (lines.length === 0) return null;

  const objects: Record<string, unknown>[] = [];
  for (const line of lines) {
    try {
      const row = JSON.parse(line) as Record<string, unknown>;
      if (row && typeof row === "object" && !Array.isArray(row)) {
        objects.push(row);
      }
    } catch {
      return null;
    }
  }

  if (objects.length === 0) return null;

  const columns = Object.keys(objects[0]!);
  if (columns.length === 0) return null;

  return {
    columns,
    rows: objects.map((obj) => columns.map((col) => obj[col])),
  };
}

export function isWrenToolError(text: string): boolean {
  return (
    text.startsWith("ERROR") ||
    text.startsWith("WREN ERROR")
  );
}
