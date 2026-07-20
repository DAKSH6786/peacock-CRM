import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  createKeyResult,
  keyResultCreateSchema,
  keyResultValueUpdateSchema,
  recordKeyResultValue,
  addKeyResultComment,
} from "@/modules/progress";
import { requirePermission } from "@/permissions";

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = await request.json();
    const action = body.action as string | undefined;

    if (action === "record-value") {
      const { keyResultId, ...rest } = body;
      const parsed = keyResultValueUpdateSchema.parse(rest);
      const keyResult = await recordKeyResultValue({
        user,
        organizationId: user.organizationId,
        keyResultId: String(keyResultId),
        ...parsed,
      });
      return NextResponse.json({ keyResult });
    }

    if (action === "comment") {
      const comment = await addKeyResultComment({
        user,
        organizationId: user.organizationId,
        keyResultId: String(body.keyResultId),
        body: String(body.body ?? ""),
      });
      return NextResponse.json({ comment });
    }

    const parsed = keyResultCreateSchema.parse(body);
    const keyResult = await createKeyResult({
      user,
      organizationId: user.organizationId,
      data: parsed,
    });
    return NextResponse.json({ keyResult });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
