import "server-only";

import type { SessionUser } from "@/permissions";
import { getDefinitionOrThrow, requireReportAccess } from "@/modules/reports/access";
import type { ReportDateRange, ReportPayload } from "@/modules/reports/types";
import { runCompanyReport } from "@/modules/reports/services/company";
import { runCrmReport } from "@/modules/reports/services/crm";
import { runDeliveryReport } from "@/modules/reports/services/delivery";
import { runFinanceReport } from "@/modules/reports/services/finance";
import { runHrReport } from "@/modules/reports/services/hr";
import { runSalesReport } from "@/modules/reports/services/sales";
import { runXymeReport } from "@/modules/reports/services/xyme";

export async function runReport(
  user: SessionUser | null | undefined,
  reportKey: string,
  range: ReportDateRange,
): Promise<ReportPayload> {
  const definition = getDefinitionOrThrow(reportKey);
  const authed = requireReportAccess(user, definition);
  const input = {
    key: reportKey,
    definition,
    user: authed,
    range,
  };

  switch (definition.category) {
    case "company":
      return runCompanyReport(input);
    case "crm":
      return runCrmReport(input);
    case "sales":
      return runSalesReport(input);
    case "xyme":
      return runXymeReport(input);
    case "hr":
      return runHrReport(input);
    case "delivery":
      return runDeliveryReport(input);
    case "finance":
      return runFinanceReport(input);
  }
}

