import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-lg py-16 text-center">
      <h1 className="font-[family-name:var(--font-display)] text-2xl">
        Page not found
      </h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        The page you requested does not exist in Peacock One.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex h-10 items-center justify-center rounded-md bg-[var(--brand)] px-4 text-sm font-medium text-[var(--brand-foreground)] hover:bg-[var(--brand-hover)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
