import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { IMPORT_CATALOG, getImportDefinition, buildCsvTemplate } from "@/modules/imports";
import { createImportJob, listImportHistory } from "@/modules/imports/service";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";
import type { ImportEntityType } from "@/modules/imports";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "imports:run");

  if (!user?.organizationId) {
    return NextResponse.json({ error: "No organization" }, { status: 400 });
  }

    const history = await listImportHistory(user.organizationId);
    const catalog = IMPORT_CATALOG.filter((item) =>
      hasPermission(user.role as MembershipRole | null, item.permission),
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
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = (await request.json()) as {
      entityType: ImportEntityType;
      csvText: string;
      fileName?: string;
      columnMapping?: Record<string, string>;
      duplicatePolicy?: "SKIP" | "UPDATE" | "FAIL";
      partialPolicy?: "COMMIT_VALID" | "ALL_OR_NOTHING";
      templateOnly?: boolean;
    };

    if (body.templateOnly) {
      const definition = getImportDefinition(body.entityType);
      if (!definition) {
        return NextResponse.json({ error: "Unknown entity" }, { status: 400 });
      }
      if (!hasPermission(user.role as MembershipRole | null, definition.permission)) {
        return NextResponse.json({ error: "Forbidden" }, { status: 403 });
      }
      const csv = buildCsvTemplate(definition);
      return new NextResponse(csv, {
        headers: {
          "content-type": "text/csv",
          "content-disposition": `attachment; filename="${body.entityType}-template.csv"`,
        },
      });
    }

    const result = await createImportJob({
      user,
      organizationId: user.organizationId,
      entityType: body.entityType,
      csvText: body.csvText,
      fileName: body.fileName ?? `${body.entityType}.csv`,
      columnMapping: body.columnMapping,
      duplicatePolicy: body.duplicatePolicy,
      partialPolicy: body.partialPolicy,
    });

    if (!result.ok) {
      return NextResponse.json(
        {
          error: "Validation failed",
          validation: result.prepared.validation,
          preview: result.prepared.preview,
        },
        { status: 422 },
      );
    }

    return NextResponse.json({
      job: result.job,
      validation: result.prepared.validation,
      preview: result.prepared.preview,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    const status = message === "Forbidden" ? 403 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
