import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  createObjective,
  listObjectives,
  objectiveCreateSchema,
} from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export async function GET(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const url = new URL(request.url);
    const objectives = await listObjectives({
      organizationId: user.organizationId,
      scope: url.searchParams.get("scope") ?? undefined,
      departmentId: url.searchParams.get("departmentId") ?? undefined,
      quarter: url.searchParams.get("quarter") ?? undefined,
      health: url.searchParams.get("health") ?? undefined,
      parentId: url.searchParams.has("parentId")
        ? url.searchParams.get("parentId")
        : undefined,
    });

    return NextResponse.json({
      objectives,
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
    const parsed = objectiveCreateSchema.parse(body);
    const objective = await createObjective({
      user,
      organizationId: user.organizationId,
      data: parsed,
    });
    return NextResponse.json({ objective });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
