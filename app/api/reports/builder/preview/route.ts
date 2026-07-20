import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { executeBuilderReport } from "@/modules/reports/builder/execute";
import { ForbiddenError, UnauthorizedError } from "@/permissions";

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    const url = new URL(request.url);
    const body = (await request.json()) as { definition?: unknown };

    const payload = await executeBuilderReport({
      user,
      definition: body.definition,
      from: url.searchParams.get("from"),
      to: url.searchParams.get("to"),
    });

    return NextResponse.json(payload);
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    if (error instanceof ForbiddenError) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
    console.error("Builder preview failed", error);
    return NextResponse.json({ error: "Preview failed" }, { status: 500 });
  }
}
