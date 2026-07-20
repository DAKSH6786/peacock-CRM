import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { EXPORT_CATALOG, canAccessExports, canRequestExport } from "@/modules/exports";
import {
  approveExportJob,
  createExportJob,
  getExportDownload,
  listExportHistory,
} from "@/modules/exports/service";
import { ForbiddenError } from "@/permissions";
import type { ExportType } from "@/modules/exports";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    if (!user || !canAccessExports(user)) {
      throw new ForbiddenError("Missing export access");
    }

    if (!user.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const history = await listExportHistory(user.organizationId);
    const catalog = EXPORT_CATALOG.filter((item) =>
      canRequestExport(user, item.key),
    );

    return NextResponse.json({ catalog, history });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    if (!user || !canAccessExports(user)) {
      throw new ForbiddenError("Missing export access");
    }

    if (!user.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = (await request.json()) as {
      action?: "create" | "approve" | "download";
      exportType?: ExportType;
      columns?: string[];
      dateFrom?: string;
      dateTo?: string;
      exportJobId?: string;
      approve?: boolean;
      reason?: string;
    };

    if (body.action === "approve" && body.exportJobId) {
      if (!hasPermission(user.role as MembershipRole | null, "approvals:decide")) {
        return NextResponse.json({ error: "Forbidden" }, { status: 403 });
      }
      const job = await approveExportJob({
        user,
        organizationId: user.organizationId,
        exportJobId: body.exportJobId,
        approve: body.approve !== false,
        reason: body.reason,
      });
      return NextResponse.json({ job });
    }

    if (body.action === "download" && body.exportJobId) {
      const result = await getExportDownload({
        user,
        organizationId: user.organizationId,
        exportJobId: body.exportJobId,
      });
      if (!result.ok) {
        return NextResponse.json({ error: result.reason }, { status: 400 });
      }
      return NextResponse.json(result);
    }

    if (!body.exportType) {
      return NextResponse.json({ error: "exportType required" }, { status: 400 });
    }

    const job = await createExportJob({
      user,
      organizationId: user.organizationId,
      exportType: body.exportType,
      columns: body.columns,
      dateFrom: body.dateFrom,
      dateTo: body.dateTo,
    });

    return NextResponse.json({ job });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    const status = message === "Forbidden" ? 403 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
