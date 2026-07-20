import type { MembershipRole } from "@prisma/client";

import type { ReportDefinition } from "@/modules/reports/types";
import type { SessionUser } from "@/permissions/types";
import { hasPermission } from "@/permissions/types";

export function canExportReport(
  user: SessionUser,
  definition: ReportDefinition,
): boolean {
  if (!definition.exportable) return false;
  return hasPermission(user.role as MembershipRole | null, "reports:export");
}

export function stripRestrictedExportFields<T extends Record<string, unknown>>(
  row: T,
  definition: ReportDefinition,
  user: SessionUser,
): T {
  const restricted = definition.restrictedExportFields ?? [];
  if (restricted.length === 0) return row;

  const canSeeCompensation = hasPermission(
    user.role as MembershipRole | null,
    "employees:view_compensation",
  );
  const canSeeProfitability = hasPermission(
    user.role as MembershipRole | null,
    "finance:view_profitability",
  );

  const next = { ...row };
  for (const field of restricted) {
    const isComp =
      field.includes("cost") ||
      field.includes("payroll") ||
      field.includes("commission");
    const isProfit =
      field.includes("margin") ||
      field.includes("profit") ||
      field.includes("cost");
    if ((isComp && !canSeeCompensation) || (isProfit && !canSeeProfitability)) {
      delete next[field];
    }
  }
  return next;
}
