import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
  trend?: {
    value: string;
    direction: "up" | "down" | "flat";
  };
  className?: string;
};

export function MetricCard({
  label,
  value,
  hint,
  trend,
  className,
}: MetricCardProps) {
  return (
    <Card className={cn("feather-motif", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-[var(--muted)]">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight">
          {value}
        </p>
        <div className="mt-2 flex items-center gap-2 text-xs">
          {trend ? (
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-semibold",
                trend.direction === "up" &&
                  "bg-emerald-500/15 text-[var(--success)]",
                trend.direction === "down" &&
                  "bg-red-400/15 text-[var(--danger)]",
                trend.direction === "flat" &&
                  "bg-[var(--surface-muted)] text-[var(--muted)]",
              )}
            >
              {trend.direction === "up" ? (
                <TrendingUp className="h-3 w-3" aria-hidden />
              ) : null}
              {trend.direction === "down" ? (
                <TrendingDown className="h-3 w-3" aria-hidden />
              ) : null}
              <span>{trend.value}</span>
            </span>
          ) : null}
          {hint ? <span className="text-[var(--muted)]">{hint}</span> : null}
        </div>
      </CardContent>
    </Card>
  );
}

export function TrendIndicator({
  value,
  direction,
}: {
  value: string;
  direction: "up" | "down" | "flat";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-xs font-semibold",
        direction === "up" && "text-[var(--success)]",
        direction === "down" && "text-[var(--danger)]",
        direction === "flat" && "text-[var(--muted)]",
      )}
    >
      {direction === "up" ? <TrendingUp className="h-3.5 w-3.5" /> : null}
      {direction === "down" ? <TrendingDown className="h-3.5 w-3.5" /> : null}
      {value}
    </span>
  );
}
