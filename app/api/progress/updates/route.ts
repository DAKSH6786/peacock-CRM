import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  getUpdateReminders,
  listProgressUpdates,
  progressUpdateSchema,
  reviewProgressUpdate,
  submitProgressUpdate,
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

    const [updates, reminders] = await Promise.all([
      listProgressUpdates(user.organizationId),
      getUpdateReminders(user.organizationId),
    ]);

    return NextResponse.json({
      updates,
      reminders,
      canReview: hasPermission(
        user.role as MembershipRole | null,
        "progress:review",
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
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = await request.json();
    const action = body.action as string | undefined;

    if (action === "review") {
      requirePermission(user, "progress:review");
      const update = await reviewProgressUpdate({
        user,
        organizationId: user.organizationId,
        updateId: String(body.updateId),
        note: body.note ? String(body.note) : undefined,
      });
      return NextResponse.json({ update });
    }

    requirePermission(user, "progress:manage");
    const parsed = progressUpdateSchema.parse(body);
    const update = await submitProgressUpdate({
      user,
      organizationId: user.organizationId,
      data: parsed,
    });
    return NextResponse.json({ update });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
