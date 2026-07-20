import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  getObjectiveDetail,
  objectiveUpdateSchema,
  updateObjective,
} from "@/modules/progress";
import { requirePermission } from "@/permissions";

type Params = { params: Promise<{ objectiveId: string }> };

export async function GET(_request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const { objectiveId } = await params;
    const objective = await getObjectiveDetail(
      user.organizationId,
      objectiveId,
    );
    if (!objective) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ objective });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function PATCH(request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const { objectiveId } = await params;
    const body = await request.json();
    const parsed = objectiveUpdateSchema.parse(body);
    const objective = await updateObjective({
      user,
      organizationId: user.organizationId,
      objectiveId,
      data: parsed,
    });
    return NextResponse.json({ objective });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
