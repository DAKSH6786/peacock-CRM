export default function AppLoading() {
  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <div className="h-8 w-48 animate-pulse rounded bg-[var(--surface-muted)]" />
      <div className="h-4 w-96 max-w-full animate-pulse rounded bg-[var(--surface-muted)]" />
      <div className="mt-8 h-40 animate-pulse rounded-xl bg-[var(--surface-muted)]" />
      <span className="sr-only">Loading</span>
    </div>
  );
}
