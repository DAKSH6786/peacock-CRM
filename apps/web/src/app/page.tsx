"use client";

import { useState } from "react";

import { ArchitecturePanel } from "@/components/architecture-panel";
import { CrawlConsole } from "@/components/crawl-console";
import { HealthCard } from "@/components/health-card";
import { LoginForm } from "@/components/login-form";
import { SeoAuditPanel } from "@/components/seo-audit-panel";
import { ShareOfAnswerPanel } from "@/components/share-of-answer-panel";
import { StrategicIntelligencePanel } from "@/components/strategic-intelligence-panel";

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
          Complex strategy decomposes into Layers 0–10: classify, assemble
          relevant context, gather deterministic evidence, research, reason,
          challenge, verify, decide, simulate, plan, and learn.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <HealthCard />
        <LoginForm />
      </div>

      <CrawlConsole onCrawlIdChange={setCrawlId} />
      <SeoAuditPanel crawlId={crawlId} />
      <ShareOfAnswerPanel />
      <StrategicIntelligencePanel />
      <ArchitecturePanel />
    </main>
  );
}
