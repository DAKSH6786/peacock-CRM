import { Inbox } from "lucide-react";

import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "peacock-card flex flex-col items-center justify-center gap-3 px-6 py-16 text-center",
        className,
      )}
      role="status"
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent-teal)]">
        <Inbox className="h-5 w-5" aria-hidden />
      </span>
      <div>
        <h2 className="font-[family-name:var(--font-display)] text-lg font-semibold">
          {title}
        </h2>
        <p className="mt-1 max-w-md text-sm text-[var(--muted)]">
          {description}
        </p>
      </div>
      {action}
    </div>
  );
}
