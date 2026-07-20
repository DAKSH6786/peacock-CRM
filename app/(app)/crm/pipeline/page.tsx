import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { PipelineKanban } from "@/components/crm/pipeline-kanban";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { toSessionUser } from "@/lib/session-user";
import { getCrmLookups, getPipelineBoard } from "@/modules/crm";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Pipeline",
};

export default async function PipelinePage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const organizationId = user!.organizationId!;
  const [board, lookups] = await Promise.all([
    getPipelineBoard({ organizationId }),
    getCrmLookups(organizationId),
  ]);

  return (
    <div>
      <PageHeader
        title="Lead pipeline"
        description="Drag-and-drop kanban with stage gates, stale warnings, and close confirmation."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/crm/leads">Table view</Link>
            </Button>
            {hasPermission(user!.role as MembershipRole | null, "crm:manage") ? (
              <Button asChild>
                <Link href="/crm/leads/new">New lead</Link>
              </Button>
            ) : null}
          </>
        }
      />

      {!board ? (
        <p className="text-sm text-[var(--muted)]">
          No pipeline configured. Seed defaults or create a pipeline in settings.
        </p>
      ) : (
        <PipelineKanban
          pipelineName={board.pipeline.name}
          lostReasons={lookups.lostReasons}
          canManage={hasPermission(
            user!.role as MembershipRole | null,
            "crm:manage",
          )}
          initialColumns={board.columns.map((col) => ({
            ...col,
            stage: {
              ...col.stage,
              requiredFields: col.stage.requiredFields,
            },
            cards: col.cards.map((card) => ({
              ...card,
              probability: card.probability ?? col.stage.probability,
            })),
          }))}
        />
      )}
    </div>
  );
}
