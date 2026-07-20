import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  listDuplicateReviews,
  reviewDuplicate,
} from "@/modules/crm";
import { requirePermission } from "@/permissions";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }
    const candidates = await listDuplicateReviews(user.organizationId);
    return NextResponse.json({ candidates });
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
    await reviewDuplicate({
      user,
      organizationId: user.organizationId,
      candidateId: body.candidateId,
      decision: body.decision === "KEEP_BOTH" ? "KEEP_BOTH" : "DISMISS",
    });
    return NextResponse.json({ ok: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
