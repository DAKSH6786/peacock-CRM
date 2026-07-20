import { cn } from "@/lib/utils";

const HEALTH_STYLES: Record<string, string> = {
  GREEN: "bg-emerald-500/15 text-emerald-700 border-emerald-500/30",
  AMBER: "bg-amber-500/15 text-amber-800 border-amber-500/30",
  RED: "bg-rose-500/15 text-rose-700 border-rose-500/30",
  GREY: "bg-slate-500/10 text-slate-600 border-slate-400/30",
};

const HEALTH_LABELS: Record<string, string> = {
  GREEN: "On track",
  AMBER: "At risk",
  RED: "Off track",
  GREY: "Not started",
};

export function HealthBadge({
  health,
  className,
}: {
  health: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium",
        HEALTH_STYLES[health] ?? HEALTH_STYLES.GREY,
        className,
      )}
    >
      {HEALTH_LABELS[health] ?? health}
    </span>
  );
}

export function ProgressBar({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className={cn(
        "h-2 w-full overflow-hidden rounded-full bg-[var(--muted)]/20",
        className,
      )}
    >
      <div
        className="h-full rounded-full bg-[var(--accent)] transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function formatMinor(value: number | null | undefined, currency = "INR") {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value / 100);
}
