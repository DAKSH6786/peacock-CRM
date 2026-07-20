import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { getBusinessReview } from "@/modules/progress";
import { requirePermission } from "@/permissions";

type Params = { params: Promise<{ reviewId: string }> };

export async function GET(_request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "progress:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const { reviewId } = await params;
    const review = await getBusinessReview(user.organizationId, reviewId);
    if (!review) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ review });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}
