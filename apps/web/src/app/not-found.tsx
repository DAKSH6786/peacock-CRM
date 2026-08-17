import Link from "next/link";

const ROUTES = [
  { href: "/", label: "Command Centre" },
  { href: "/os", label: "Peacock One OS" },
  { href: "/ops", label: "Platform ops" },
  { href: "/executive", label: "Executive Brain" },
  { href: "/research", label: "Research Mode" },
  { href: "/architecture", label: "Architecture map" },
] as const;

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-8 px-6 py-16">
      <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">404</p>
      <h1
        className="text-4xl font-bold tracking-tight"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Route not found
      </h1>
      <p className="text-lg text-[var(--muted)]">
        Open the product on port <strong>3000</strong> (Next.js). Port{" "}
        <strong>8000</strong> is the API only — use{" "}
        <code className="text-[var(--primary)]">/docs</code> or{" "}
        <code className="text-[var(--primary)]">/health</code> there, not as the UI.
      </p>
      <ul className="space-y-2 text-base">
        {ROUTES.map((route) => (
          <li key={route.href}>
            <Link className="text-[var(--primary)] underline-offset-4 hover:underline" href={route.href}>
              {route.label}
              <span className="ml-2 text-[var(--muted)]">{route.href}</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
