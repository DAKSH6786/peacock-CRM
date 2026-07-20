import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  bulkAssignSchema,
  bulkStageSchema,
  bulkTagsSchema,
  createLead,
  getCrmLookups,
  leadCreateSchema,
  listLeads,
  bulkAssignLeads,
  bulkChangeStage,
  bulkManageTags,
} from "@/modules/crm";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export async function GET(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "crm:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const url = new URL(request.url);
    const filters = {
      q: url.searchParams.get("q") ?? undefined,
      sourceId: url.searchParams.get("sourceId") ?? undefined,
      statusId: url.searchParams.get("statusId") ?? undefined,
      stageId: url.searchParams.get("stageId") ?? undefined,
      pipelineId: url.searchParams.get("pipelineId") ?? undefined,
      assignedUserId: url.searchParams.get("assignedUserId") ?? undefined,
      country: url.searchParams.get("country") ?? undefined,
      tagId: url.searchParams.get("tagId") ?? undefined,
      followUp: (url.searchParams.get("followUp") as
        | "overdue"
        | "upcoming"
        | "none"
        | null) ?? undefined,
    };

    const [leads, lookups] = await Promise.all([
      listLeads({ organizationId: user.organizationId, filters }),
      getCrmLookups(user.organizationId),
    ]);

    return NextResponse.json({
      leads,
      lookups,
      canManage: hasPermission(user.role as MembershipRole | null, "crm:manage"),
      canExport: hasPermission(user.role as MembershipRole | null, "reports:export") ||
        hasPermission(user.role as MembershipRole | null, "crm:view"),
    });
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
    const action = body.action as string | undefined;

    if (action === "bulk-assign") {
      const parsed = bulkAssignSchema.parse(body);
      const result = await bulkAssignLeads({
        user,
        organizationId: user.organizationId,
        ...parsed,
      });
      return NextResponse.json(result);
    }

    if (action === "bulk-stage") {
      const parsed = bulkStageSchema.parse(body);
      const result = await bulkChangeStage({
        user,
        organizationId: user.organizationId,
        ...parsed,
      });
      return NextResponse.json({ results: result });
    }

    if (action === "bulk-tags") {
      const parsed = bulkTagsSchema.parse(body);
      const result = await bulkManageTags({
        user,
        organizationId: user.organizationId,
        ...parsed,
      });
      return NextResponse.json(result);
    }

    const parsed = leadCreateSchema.parse(body);
    const lead = await createLead({
      user,
      organizationId: user.organizationId,
      data: parsed,
    });
    return NextResponse.json({ lead });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
