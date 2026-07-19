import { Inbox } from "lucide-react";

type EmptyStateProps = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] px-6 py-16 text-center"
      role="status"
    >
      <Inbox className="h-8 w-8 text-[var(--muted)]" aria-hidden />
      <div>
        <h2 className="font-[family-name:var(--font-display)] text-lg">
          {title}
        </h2>
        <p className="mt-1 max-w-md text-sm text-[var(--muted)]">
          {description}
        </p>
      </div>
    </div>
  );
}
