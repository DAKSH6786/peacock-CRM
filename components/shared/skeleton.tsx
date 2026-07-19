import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-[var(--surface-hover)]",
        className,
      )}
      {...props}
    />
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div
      className="peacock-card overflow-hidden"
      role="status"
      aria-live="polite"
    >
      <div className="border-b border-[var(--border)] p-4">
        <Skeleton className="h-4 w-40" />
      </div>
      <div className="space-y-3 p-4">
        {Array.from({ length: rows }).map((_, index) => (
          <Skeleton key={index} className="h-10 w-full" />
        ))}
      </div>
      <span className="sr-only">Loading table</span>
    </div>
  );
}
