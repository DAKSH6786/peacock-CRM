import type { Metadata } from "next";

import { auth } from "@/auth";
import { DashboardView } from "@/components/dashboard/dashboard-view";
import { toSessionUser } from "@/lib/session-user";
import { parseDashboardRange } from "@/modules/dashboard/date-range";
import { getDashboardPayload } from "@/modules/dashboard/metrics.service";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Dashboard",
};

type DashboardPageProps = {
  searchParams: Promise<{ from?: string; to?: string }>;
};

export default async function DashboardPage({
  searchParams,
}: DashboardPageProps) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "dashboard:view");

  const params = await searchParams;
  const range = parseDashboardRange(params.from, params.to);
  const payload = await getDashboardPayload(user!, range);

  return <DashboardView payload={payload} />;
}
