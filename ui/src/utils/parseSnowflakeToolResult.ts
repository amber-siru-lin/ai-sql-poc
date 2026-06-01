export type SnowflakeQueryResult = {
  columns: string[];
  rows: unknown[][];
};

/** Parse execute_snowflake_sql tool output from the Python agent. */
export function parseSnowflakeToolResult(text: string): SnowflakeQueryResult | null {
  if (!text || text.startsWith("ERROR:") || text.startsWith("SNOWFLAKE ERROR:")) {
    return null;
  }

  const colsMatch = text.match(/Columns:\s*(\[[\s\S]*?\])\s*\n/i);
  const rowsMatch = text.match(/Rows[^\n]*:\s*\n?([\s\S]*)$/i);
  if (!colsMatch) return null;

  try {
    const columns = parsePythonishList(colsMatch[1]) as string[];
    if (!Array.isArray(columns) || columns.length === 0) return null;

    const rowsRaw = rowsMatch?.[1]?.trim();
    const rows = rowsRaw ? (parsePythonishList(rowsRaw) as unknown[][]) : [];
    if (!Array.isArray(rows)) return null;

    return { columns, rows: rows.map(normalizeRow) };
  } catch {
    return null;
  }
}

function normalizeRow(row: unknown): unknown[] {
  if (Array.isArray(row)) return row;
  if (row && typeof row === "object") return Object.values(row as Record<string, unknown>);
  return [row];
}

/** Coerce Python-ish literals to JSON-parseable text. */
function parsePythonishList(source: string): unknown {
  let s = source.trim();
  s = s.replace(/Decimal\('([^']*)'\)/g, "$1");
  s = s.replace(/Decimal\("([^"]*)"\)/g, "$1");
  s = s.replace(/\bNone\b/g, "null");
  s = s.replace(/\bTrue\b/g, "true");
  s = s.replace(/\bFalse\b/g, "false");
  s = s.replace(/'/g, '"');
  return JSON.parse(s);
}

export type ChartSeries = {
  labelKey: string;
  valueKey: string;
  data: { label: string; value: number }[];
};

/** Build a simple bar/line series when we have a label column and a numeric measure. */
export function buildChartSeries(result: SnowflakeQueryResult): ChartSeries | null {
  const { columns, rows } = result;
  if (rows.length === 0 || columns.length < 2) return null;

  const numericIdx = columns.findIndex((_, i) =>
    rows.every((row) => {
      const v = row[i];
      return v === null || v === undefined || !Number.isNaN(Number(v));
    }),
  );
  if (numericIdx < 0) return null;

  let labelIdx = 0;
  if (labelIdx === numericIdx) labelIdx = numericIdx === 0 ? 1 : 0;

  const data = rows
    .map((row) => ({
      label: String(row[labelIdx] ?? ""),
      value: Number(row[numericIdx]),
    }))
    .filter((d) => d.label && !Number.isNaN(d.value));

  if (data.length === 0) return null;

  return {
    labelKey: columns[labelIdx] ?? "category",
    valueKey: columns[numericIdx] ?? "value",
    data,
  };
}
