import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const tones = {
  default:
    "bg-[var(--surface-muted)] text-[var(--foreground)] border-[var(--border)]",
  success: "bg-emerald-500/15 text-[var(--success)] border-emerald-500/25",
  warning: "bg-amber-400/15 text-[var(--warning)] border-amber-400/25",
  danger: "bg-red-400/15 text-[var(--danger)] border-red-400/25",
  info: "bg-sky-400/15 text-[var(--info)] border-sky-400/25",
  teal: "bg-[var(--accent-soft)] text-[var(--accent-teal)] border-teal-400/25",
  violet: "bg-violet-500/15 text-[var(--accent-violet)] border-violet-500/25",
} as const;

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: keyof typeof tones;
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}

/** Status badge helper for common workflow statuses */
export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase();
  const tone =
    normalized.includes("APPROV") ||
    normalized.includes("ACTIVE") ||
    normalized.includes("WON") ||
    normalized.includes("PAID")
      ? "success"
      : normalized.includes("PENDING") ||
          normalized.includes("DRAFT") ||
          normalized.includes("REVIEW")
        ? "warning"
        : normalized.includes("REJECT") ||
            normalized.includes("LOST") ||
            normalized.includes("OVERDUE")
          ? "danger"
          : "teal";

  return <Badge tone={tone}>{status}</Badge>;
}
