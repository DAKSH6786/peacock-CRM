import "server-only";

import type { MembershipRole } from "@prisma/client";

import { prisma } from "@/database";
import {
  builderDefinitionSchema,
  type BuilderDefinition,
} from "@/modules/reports/builder/datasets";
import type { SessionUser } from "@/permissions";
import { ForbiddenError, requireOrganization } from "@/permissions";
import { hasPermission } from "@/permissions/types";

export async function saveBuilderReport(input: {
  user: SessionUser | null | undefined;
  name: string;
  description?: string;
  definition: unknown;
  chartType?: string;
  shareRoles?: string[];
  schedule?: { cadence: "daily" | "weekly" | "monthly"; format: "csv" | "spreadsheet" | "pdf" };
}) {
  const authed = requireOrganization(input.user);
  if (!hasPermission(authed.role as MembershipRole | null, "reports:view")) {
    throw new ForbiddenError("Missing permission: reports:view");
  }

  const definition = builderDefinitionSchema.parse(input.definition) satisfies BuilderDefinition;

  const saved = await prisma.savedReport.create({
    data: {
      organizationId: authed.organizationId,
      ownerUserId: authed.id,
      name: input.name.trim(),
      description: input.description?.trim() || null,
      source: "builder",
      definition,
      chartType: input.chartType ?? definition.chartType,
    },
  });

  if (input.shareRoles?.length) {
    await prisma.reportShare.createMany({
      data: input.shareRoles.map((roleCode) => ({
        organizationId: authed.organizationId,
        savedReportId: saved.id,
        roleCode,
        canExport: hasPermission(authed.role as MembershipRole | null, "reports:export"),
      })),
    });
  }

  if (input.schedule) {
    const nextRunAt = new Date();
    if (input.schedule.cadence === "daily") nextRunAt.setUTCDate(nextRunAt.getUTCDate() + 1);
    if (input.schedule.cadence === "weekly") nextRunAt.setUTCDate(nextRunAt.getUTCDate() + 7);
    if (input.schedule.cadence === "monthly") nextRunAt.setUTCMonth(nextRunAt.getUTCMonth() + 1);

    await prisma.reportSchedule.create({
      data: {
        organizationId: authed.organizationId,
        savedReportId: saved.id,
        cadence: input.schedule.cadence,
        format: input.schedule.format,
        nextRunAt,
        createdById: authed.id,
      },
    });
  }

  return saved;
}

export async function listSavedReports(user: SessionUser | null | undefined) {
  const authed = requireOrganization(user);
  const role = authed.role as MembershipRole | null;

  return prisma.savedReport.findMany({
    where: {
      organizationId: authed.organizationId,
      deletedAt: null,
      OR: [
        { ownerUserId: authed.id },
        role ? { shares: { some: { roleCode: role } } } : undefined,
      ].filter(Boolean) as never,
    },
    orderBy: { updatedAt: "desc" },
    include: {
      shares: true,
      schedules: { where: { isActive: true } },
    },
    take: 100,
  });
}
