"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ChartPoint = {
  label: string;
  value: number;
};

type ChartCardProps = {
  title: string;
  description?: string;
  data: ChartPoint[];
  valueLabel?: string;
};

export function ChartCard({
  title,
  description,
  data,
  valueLabel = "Value",
}: ChartCardProps) {
  const summary = data
    .map((point) => `${point.label}: ${point.value}`)
    .join("; ");

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        <div
          className="h-64 w-full"
          role="img"
          aria-label={`${title}. ${summary}`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: "var(--muted)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "var(--muted)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  color: "var(--foreground)",
                }}
              />
              <Bar
                dataKey="value"
                name={valueLabel}
                fill="var(--accent-teal)"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="sr-only">{summary}</p>
        <ul className="mt-3 grid gap-1 text-xs text-[var(--muted)] md:grid-cols-2">
          {data.map((point) => (
            <li key={point.label}>
              {point.label}:{" "}
              <span className="text-[var(--foreground)]">{point.value}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
