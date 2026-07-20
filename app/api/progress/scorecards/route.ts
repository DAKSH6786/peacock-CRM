import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  DEPARTMENT_KPI_TEMPLATES,
  ensureDepartmentScorecard,
  listScorecards,
  scorecardSchema,
} from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const scorecards = await listScorecards(user.organizationId);
    return NextResponse.json({
      scorecards,
      templates: DEPARTMENT_KPI_TEMPLATES,
      canManage: hasPermission(
        user.role as MembershipRole | null,
        "progress:manage",
      ),
    });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = await request.json();
    const parsed = scorecardSchema.parse(body);
    const scorecard = await ensureDepartmentScorecard({
      user,
      organizationId: user.organizationId,
      departmentId: parsed.departmentId,
      name: parsed.name,
      description: parsed.description,
      kpiIds: parsed.kpiIds,
      templateCode: body.templateCode ? String(body.templateCode) : undefined,
    });
    return NextResponse.json({ scorecard });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
