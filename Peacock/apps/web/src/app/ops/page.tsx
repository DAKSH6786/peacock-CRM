"use client";

import Link from "next/link";
import { useState } from "react";

import { ArchitecturePanel } from "@/components/architecture-panel";
import { CrawlConsole } from "@/components/crawl-console";
import { HealthCard } from "@/components/health-card";
import { SeoAuditPanel } from "@/components/seo-audit-panel";
import { StrategicIntelligencePanel } from "@/components/strategic-intelligence-panel";

export default function OpsPage() {
  const [crawlId, setCrawlId] = useState<string | null>(null);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-12">
      <header className="space-y-4">
        <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">
          <Link href="/" className="hover:text-[var(--primary)]">
            ← Command Centre
          </Link>
        </p>
        <h1
          className="max-w-3xl text-4xl font-bold tracking-tight md:text-5xl"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Platform ops
        </h1>
        <p className="max-w-2xl text-lg text-[var(--muted)]">
          Crawl, audit, and strategic intelligence tooling — secondary to the
          Peacock Command Centre.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <HealthCard />
      </div>

      <CrawlConsole onCrawlIdChange={setCrawlId} />
      <SeoAuditPanel crawlId={crawlId} />
      <StrategicIntelligencePanel />
      <ArchitecturePanel />
    </main>
  );
}
