import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  activitySchema,
  completeFollowUp,
  convertLead,
  convertLeadSchema,
  createFollowUp,
  createQuoteFromLead,
  followUpSchema,
  getLeadDetail,
  leadUpdateSchema,
  logLeadActivity,
  moveLeadStage,
  rescheduleFollowUp,
  stageMoveSchema,
  updateLead,
} from "@/modules/crm";
import { requirePermission } from "@/permissions";

type Params = { params: Promise<{ leadId: string }> };

export async function GET(_request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }
    const { leadId } = await params;
    const lead = await getLeadDetail(user.organizationId, leadId);
    if (!lead) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ lead });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function PATCH(request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }
    const { leadId } = await params;
    const body = await request.json();
    const parsed = leadUpdateSchema.parse(body);
    const lead = await updateLead({
      user,
      organizationId: user.organizationId,
      leadId,
      data: parsed,
    });
    return NextResponse.json({ lead });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

export async function POST(request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }
    const { leadId } = await params;
    const body = await request.json();
    const action = body.action as string;

    if (action === "move-stage") {
      const parsed = stageMoveSchema.parse(body);
      const result = await moveLeadStage({
        user,
        organizationId: user.organizationId,
        leadId,
        ...parsed,
      });
      return NextResponse.json(result);
    }

    if (action === "convert") {
      const parsed = convertLeadSchema.parse(body);
      const result = await convertLead({
        user,
        organizationId: user.organizationId,
        leadId,
        options: parsed,
      });
      return NextResponse.json(result);
    }

    if (action === "activity") {
      const parsed = activitySchema.parse(body);
      const lead = await logLeadActivity({
        user,
        organizationId: user.organizationId,
        leadId,
        ...parsed,
      });
      return NextResponse.json({ lead });
    }

    if (action === "follow-up") {
      const parsed = followUpSchema.parse(body);
      const lead = await createFollowUp({
        user,
        organizationId: user.organizationId,
        leadId,
        ...parsed,
      });
      return NextResponse.json({ lead });
    }

    if (action === "complete-follow-up") {
      const lead = await completeFollowUp({
        user,
        organizationId: user.organizationId,
        followUpId: body.followUpId,
      });
      return NextResponse.json({ lead });
    }

    if (action === "reschedule-follow-up") {
      const lead = await rescheduleFollowUp({
        user,
        organizationId: user.organizationId,
        followUpId: body.followUpId,
        dueAt: body.dueAt,
      });
      return NextResponse.json({ lead });
    }

    if (action === "create-quote") {
      const quote = await createQuoteFromLead({
        user,
        organizationId: user.organizationId,
        leadId,
      });
      return NextResponse.json({ quote });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
