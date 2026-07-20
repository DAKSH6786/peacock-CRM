import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { saveBuilderReport } from "@/modules/reports/builder/save";
import { ForbiddenError, UnauthorizedError } from "@/permissions";

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    const body = (await request.json()) as {
      name?: string;
      description?: string;
      definition?: unknown;
      chartType?: string;
      shareRoles?: string[];
      schedule?: {
        cadence: "daily" | "weekly" | "monthly";
        format: "csv" | "spreadsheet" | "pdf";
      };
    };

    if (!body.name || !body.definition) {
      return NextResponse.json({ error: "Missing fields" }, { status: 400 });
    }

    const saved = await saveBuilderReport({
      user,
      name: body.name,
      description: body.description,
      definition: body.definition,
      chartType: body.chartType,
      shareRoles: body.shareRoles,
      schedule: body.schedule,
    });

    return NextResponse.json({ id: saved.id });
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    if (error instanceof ForbiddenError) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
    console.error("Save builder report failed", error);
    return NextResponse.json({ error: "Save failed" }, { status: 500 });
  }
}
