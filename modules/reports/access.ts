import type { MembershipRole } from "@prisma/client";

import type { Permission, SessionUser } from "@/permissions/types";
import { hasPermission } from "@/permissions/types";
import { ForbiddenError, requireOrganization } from "@/permissions";
import { prisma } from "@/database";
import type {
  ReportDefinition,
  SalesPerformanceVisibility,
} from "@/modules/reports/types";
import { getReportDefinition } from "@/modules/reports/catalog";
import {
  canExportReport,
  stripRestrictedExportFields,
} from "@/modules/reports/export-policy";

export { canExportReport, stripRestrictedExportFields };

export function requireReportAccess(
  user: SessionUser | null | undefined,
  definition: ReportDefinition,
) {
  const authed = requireOrganization(user);
  if (!hasPermission(authed.role as MembershipRole | null, definition.permission)) {
    throw new ForbiddenError(`Missing permission: ${definition.permission}`);
  }
  for (const permission of definition.extraPermissions ?? []) {
    if (!hasPermission(authed.role as MembershipRole | null, permission)) {
      throw new ForbiddenError(`Missing permission: ${permission}`);
    }
  }
  return authed;
}

export async function getSalesPerformanceVisibility(
  organizationId: string,
): Promise<SalesPerformanceVisibility> {
  const settings = await prisma.organizationSettings.findUnique({
    where: { organizationId },
    select: { salesPerformanceVisibility: true },
  });
  const raw = (settings?.salesPerformanceVisibility ?? {}) as Partial<SalesPerformanceVisibility>;
  return {
    showPeerLeaderboard: raw.showPeerLeaderboard ?? true,
    showCostVersusRevenue: raw.showCostVersusRevenue ?? false,
    salesSelfOnly: raw.salesSelfOnly ?? false,
  };
}

export function assertPermission(
  user: SessionUser,
  permission: Permission,
): void {
  if (!hasPermission(user.role as MembershipRole | null, permission)) {
    throw new ForbiddenError(`Missing permission: ${permission}`);
  }
}

export function getDefinitionOrThrow(reportKey: string): ReportDefinition {
  const definition = getReportDefinition(reportKey);
  if (!definition) {
    throw new ForbiddenError(`Unknown report: ${reportKey}`);
  }
  return definition;
}
