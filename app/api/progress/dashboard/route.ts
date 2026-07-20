import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { getCompanyProgressDashboard } from "@/modules/progress";
import { requirePermission } from "@/permissions";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const dashboard = await getCompanyProgressDashboard(user.organizationId);
    return NextResponse.json({ dashboard });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}
