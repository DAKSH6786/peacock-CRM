import type { Metadata } from "next";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import {
  expandPromptUniverse,
  promptUniverseCatalog,
} from "@/modules/prompt-universe";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Prompt Universe",
};

export default async function PromptUniversePage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");

  const catalog = promptUniverseCatalog();
  const demo = expandPromptUniverse({
    brandName: "Peacock One",
    industry: "SaaS",
    location: "eu",
    personaCodes: ["enterprise_buyer", "cfo", "technical_evaluator"],
    maxPrompts: 40,
    signals: [
      { sourceKind: "product", signalText: "CRM", productName: "CRM" },
      {
        sourceKind: "search_console_query",
        signalText: "best enterprise crm",
      },
      {
        sourceKind: "people_also_ask",
        signalText: "how to migrate from salesforce",
      },
    ],
  });

  const simple = demo.prompts.filter((p) => p.complexity === "simple").slice(0, 6);
  const contextual = demo.prompts
    .filter((p) => p.complexity === "contextual")
    .slice(0, 4);

  return (
    <div>
      <PageHeader
        title="Prompt Universe"
        description="Complete intent landscape — not a manually configured 25/50/100 prompt set. Tracks both short discovery prompts and persona-contextual shortlists."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Prompts</CardTitle>
            <CardDescription>Demo expansion</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-bold">
            {demo.prompts.length}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Families</CardTitle>
            <CardDescription>Intent clusters</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-bold">
            {demo.familyCount}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Simple</CardTitle>
            <CardDescription>e.g. best CRM</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-bold">
            {demo.simpleCount}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Contextual</CardTitle>
            <CardDescription>Persona shortlists</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-bold">
            {demo.contextualCount}
          </CardContent>
        </Card>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Prompt types</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2 text-sm">
            {catalog.promptTypes.map((t) => (
              <span
                key={t}
                className="rounded-md border border-[var(--border)] px-2 py-1"
              >
                {t.replace(/_/g, " ")}
              </span>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Synthetic personas</CardTitle>
            <CardDescription>Analytical lenses, not fake identities</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2 text-sm">
            {catalog.syntheticPersonas.map((p) => (
              <span
                key={p.code}
                className="rounded-md border border-[var(--border)] px-2 py-1"
              >
                {p.name}
              </span>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Simple prompts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {simple.map((p) => (
              <div key={p.promptHash + p.persona}>
                <p className="font-medium">{p.promptText}</p>
                <p className="text-[var(--muted)]">
                  {p.promptType} · {p.funnelStage} · {p.intent}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Contextual persona prompts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {contextual.map((p) => (
              <div key={p.promptHash + p.persona}>
                <p className="mb-1 text-xs uppercase tracking-wide text-[var(--muted)]">
                  {p.persona}
                </p>
                <p className="whitespace-pre-wrap font-medium">{p.promptText}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
