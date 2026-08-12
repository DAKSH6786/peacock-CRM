"use client";

import { useState } from "react";

import { ArchitecturePanel } from "@/components/architecture-panel";
import { CrawlConsole } from "@/components/crawl-console";
import { HealthCard } from "@/components/health-card";
import { LoginForm } from "@/components/login-form";
import { SeoAuditPanel } from "@/components/seo-audit-panel";

export default function HomePage() {
  const [crawlId, setCrawlId] = useState<string | null>(null);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-12">
      <header className="space-y-4">
        <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">
          Peacock One
        </p>
        <h1
          className="max-w-3xl text-4xl font-bold tracking-tight md:text-6xl"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Generative visibility intelligence architecture
        </h1>
        <p className="max-w-2xl text-lg text-[var(--muted)]">
          OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN. Peacock
          Crawler ingests sites; Peacock SEO Engine turns crawl data into
          deterministic, explainable audits.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <HealthCard />
        <LoginForm />
      </div>

      <CrawlConsole onCrawlIdChange={setCrawlId} />
      <SeoAuditPanel crawlId={crawlId} />
      <ArchitecturePanel />
    </main>
  );
}