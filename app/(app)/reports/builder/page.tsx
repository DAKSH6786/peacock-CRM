import type { Metadata } from "next";
import type { MembershipRole } from "@prisma/client";

import { auth } from "@/auth";
import { ReportBuilderForm } from "@/components/reports/report-builder-form";
import { PageHeader } from "@/components/shared/page-header";
import { toSessionUser } from "@/lib/session-user";
import { BUILDER_DATASETS } from "@/modules/reports/builder/datasets";
import { parseReportRange, toDateInputValue } from "@/modules/reports/date-range";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";

export const metadata: Metadata = {
  title: "Report builder",
};

type Props = {
  searchParams: Promise<{ from?: string; to?: string }>;
};

export default async function ReportBuilderPage({ searchParams }: Props) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "reports:view");

  const params = await searchParams;
  const range = parseReportRange(params.from, params.to);
  const role = user!.role as MembershipRole | null;
  const allowedDatasetIds = BUILDER_DATASETS.filter((dataset) =>
    hasPermission(role, dataset.permission),
  ).map((dataset) => dataset.id);

  return (
    <div>
      <PageHeader
        title="Report builder"
        description="Assemble constrained analytics from approved datasets. No arbitrary SQL."
      />
      <ReportBuilderForm
        allowedDatasetIds={allowedDatasetIds}
        from={toDateInputValue(range.from)}
        to={toDateInputValue(range.to)}
      />
    </div>
  );
}
