import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartSeries } from "../utils/parseSnowflakeToolResult";

type SqlResultChartProps = {
  series: ChartSeries;
};

export function SqlResultChart({ series }: SqlResultChartProps) {
  const { data, labelKey, valueKey } = series;

  return (
    <div className="sql-result-chart">
      <p className="sql-result-chart__caption">
        {valueKey} by {labelKey}
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "var(--muted)" }}
            angle={-28}
            textAnchor="end"
            height={56}
            interval={0}
          />
          <YAxis tick={{ fontSize: 11, fill: "var(--muted)" }} />
          <Tooltip
            contentStyle={{
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
