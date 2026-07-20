type ActivityItem = {
  id: string;
  title: string;
  description?: string;
  at: string;
};

export function ActivityTimeline({ items }: { items: ActivityItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-[var(--muted)]" role="status">
        No activity yet.
      </p>
    );
  }

  return (
    <ol className="space-y-4" aria-label="Activity timeline">
      {items.map((item, index) => (
        <li key={item.id} className="relative flex gap-3">
          <div className="flex flex-col items-center">
            <span className="mt-1 h-2.5 w-2.5 rounded-full bg-[var(--accent-teal)]" />
            {index < items.length - 1 ? (
              <span className="mt-1 w-px flex-1 bg-[var(--border)]" />
            ) : null}
          </div>
          <div className="pb-2">
            <p className="text-sm font-semibold">{item.title}</p>
            {item.description ? (
              <p className="mt-0.5 text-sm text-[var(--muted)]">
                {item.description}
              </p>
            ) : null}
            <p className="mt-1 text-xs text-[var(--muted)]">{item.at}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
