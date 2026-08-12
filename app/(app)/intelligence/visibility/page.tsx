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
import { prisma } from "@/database";
import { toSessionUser } from "@/lib/session-user";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "AI visibility",
};

export default async function AiVisibilityPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");

  const samples = await prisma.aiVisibilitySample.findMany({
    where: {
      property: {
        organizationId: user!.organizationId!,
        deletedAt: null,
      },
    },
    orderBy: { sampledAt: "desc" },
    take: 50,
    include: {
      property: { select: { name: true, primaryDomain: true } },
    },
  });

  const bySurface = new Map<string, { mentioned: number; total: number }>();
  for (const sample of samples) {
    const row = bySurface.get(sample.surface) ?? { mentioned: 0, total: 0 };
    row.total += 1;
    if (sample.mentionedBrand) row.mentioned += 1;
    bySurface.set(sample.surface, row);
  }

  return (
    <div>
      <PageHeader
        title="AI visibility measurement"
        description="Cross-LLM probes use VISIBILITY_PROBE templates — never THINK prompts — so measurement stays honest."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[...bySurface.entries()].map(([surface, stats]) => (
          <Card key={surface}>
            <CardHeader>
              <CardTitle>{surface}</CardTitle>
              <CardDescription>Mention rate on probe answers</CardDescription>
            </CardHeader>
            <CardContent className="text-3xl font-bold">
              {stats.total
                ? `${Math.round((stats.mentioned / stats.total) * 100)}%`
                : "—"}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent probe samples</CardTitle>
        </CardHeader>
        <CardContent>
          {samples.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No samples yet. Run the cognitive loop to MEASURE across ChatGPT,
              Gemini, Claude, Perplexity, and DeepSeek.
            </p>
          ) : (
            <ul className="space-y-3 text-sm">
              {samples.slice(0, 20).map((sample) => (
                <li
                  key={sample.id}
                  className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] pb-2"
                >
                  <span>
                    {sample.property.name} · {sample.surface}
                  </span>
                  <span className="text-[var(--muted)]">
                    {sample.mentionedBrand ? "Mentioned" : "Not mentioned"}
                    {sample.citedUrl ? " · URL cited" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
