"use client";

import Link from "next/link";

/**
 * Shared shell for Peacock One product modules (SEO/AEO/GEO Audit, Blog & Topic
 * Recommendations, Keyword & Backlink Recommendations, AI Visibility, Content
 * Optimizer). Reuses the existing `cc-shell` / `os-*` design language — no new
 * visual system is introduced.
 */
export function ModuleShell({
  title,
  kicker,
  lede,
  children,
}: {
  title: string;
  kicker: string;
  lede?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="cc-shell">
      <p className="cc-hero__kicker">{kicker}</p>
      <h1 className="cc-hero__brand" style={{ fontFamily: "var(--font-display)" }}>
        {title}
      </h1>
      {lede ? <p className="os-lede">{lede}</p> : null}
      <div className="cc-hero__actions" style={{ marginBottom: "2rem" }}>
        <Link href="/" className="cc-btn cc-btn--ghost">
          Command Centre
        </Link>
        <Link href="/os" className="cc-btn cc-btn--ghost">
          Peacock One OS
        </Link>
      </div>
      {children}
    </div>
  );
}
