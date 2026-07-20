import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { universalSearch } from "@/modules/search/universal-search.service";
import {
  ForbiddenError,
  UnauthorizedError,
  requirePermission,
} from "@/permissions";

export async function GET(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "dashboard:view");

    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q") ?? "";
    const result = await universalSearch(user!, q);

    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    if (error instanceof ForbiddenError) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
    console.error("Universal search failed", error);
    return NextResponse.json({ error: "Search failed" }, { status: 500 });
  }
}
