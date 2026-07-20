import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { getPipelineBoard, moveLeadStage, stageMoveSchema } from "@/modules/crm";
import { requirePermission } from "@/permissions";

export async function GET(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }
    const url = new URL(request.url);
    const board = await getPipelineBoard({
      organizationId: user.organizationId,
      pipelineId: url.searchParams.get("pipelineId") ?? undefined,
    });
    return NextResponse.json({ board });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }
    const body = await request.json();
    const parsed = stageMoveSchema.parse(body);
    if (!body.leadId) {
      return NextResponse.json({ error: "leadId required" }, { status: 400 });
    }
    const result = await moveLeadStage({
      user,
      organizationId: user.organizationId,
      leadId: body.leadId,
      ...parsed,
    });
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
