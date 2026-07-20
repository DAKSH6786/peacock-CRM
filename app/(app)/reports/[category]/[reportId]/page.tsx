import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { ReportViewer } from "@/components/reports/report-viewer";
import { toSessionUser } from "@/lib/session-user";
import { canExportReport, getDefinitionOrThrow } from "@/modules/reports/access";
import {
  categoryLabel,
  type ReportCategory,
} from "@/modules/reports/catalog";
import { parseReportRange } from "@/modules/reports/date-range";
import { runReport } from "@/modules/reports/runner";
import { requirePermission } from "@/permissions";

type Props = {
  params: Promise<{ category: string; reportId: string }>;
  searchParams: Promise<{ from?: string; to?: string }>;
};

const VALID: ReportCategory[] = [
  "company",
  "crm",
  "sales",
  "xyme",
  "hr",
  "delivery",
  "finance",
];

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { category, reportId } = await params;
  const key = `${category}.${reportId}`;
  try {
    const definition = getDefinitionOrThrow(key);
    return { title: definition.title };
  } catch {
    return { title: `${categoryLabel(category as ReportCategory)} report` };
  }
}

export default async function ReportDetailPage({ params, searchParams }: Props) {
  const { category, reportId } = await params;
  if (!VALID.includes(category as ReportCategory)) notFound();

  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "reports:view");

  const key = `${category}.${reportId}`;
  let definition;
  try {
    definition = getDefinitionOrThrow(key);
  } catch {
    notFound();
  }

  if (definition.category !== category) notFound();

  const query = await searchParams;
  const range = parseReportRange(query.from, query.to);
  const payload = await runReport(user, key, range);

  return (
    <ReportViewer
      payload={payload}
      canExport={canExportReport(user!, definition)}
    />
  );
}
