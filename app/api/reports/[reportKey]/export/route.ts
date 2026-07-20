import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  canExportReport,
  getDefinitionOrThrow,
  requireReportAccess,
} from "@/modules/reports/access";
import { parseReportRange } from "@/modules/reports/date-range";
import {
  buildExportRows,
  toCsv,
  toPrintableHtml,
  toSpreadsheetTsv,
} from "@/modules/reports/export";
import { runReport } from "@/modules/reports/runner";
import { ForbiddenError, UnauthorizedError } from "@/permissions";

type Params = { params: Promise<{ reportKey: string }> };

export async function GET(request: Request, { params }: Params) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    if (!user) throw new UnauthorizedError();

    const { reportKey: encoded } = await params;
    const reportKey = decodeURIComponent(encoded);
    const definition = getDefinitionOrThrow(reportKey);
    requireReportAccess(user, definition);
    if (!canExportReport(user, definition)) {
      throw new ForbiddenError("Missing permission: reports:export");
    }

    const url = new URL(request.url);
    const range = parseReportRange(
      url.searchParams.get("from"),
      url.searchParams.get("to"),
    );
    const format = (url.searchParams.get("format") ?? "csv") as
      | "csv"
      | "spreadsheet"
      | "pdf";

    const payload = await runReport(user, reportKey, range);

    if (format === "pdf") {
      const html = toPrintableHtml(payload);
      return new NextResponse(html, {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Content-Disposition": `attachment; filename="${reportKey}.html"`,
        },
      });
    }

    const { headers, rows } = buildExportRows(payload, definition, user);
    const meta = [
      `# Report: ${payload.title}`,
      `# Range: ${payload.range.label}`,
      `# Currency: ${payload.currencyCode}`,
      `# Revenue definition: ${payload.revenueDefinition ?? "n/a"}`,
      `# Refreshed: ${payload.refreshedAt}`,
      `# Summary: ${payload.summary}`,
    ];

    if (format === "spreadsheet") {
      const body = `${meta.join("\n")}\n${toSpreadsheetTsv(headers, rows)}`;
      return new NextResponse(body, {
        headers: {
          "Content-Type": "text/tab-separated-values; charset=utf-8",
          "Content-Disposition": `attachment; filename="${reportKey}.tsv"`,
        },
      });
    }

    const body = `${meta.map((line) => line.replace(/^# /, "")).join("\n")}\n${toCsv(headers, rows)}`;
    return new NextResponse(body, {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="${reportKey}.csv"`,
      },
    });
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    if (error instanceof ForbiddenError) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
    console.error("Report export failed", error);
    return NextResponse.json({ error: "Export failed" }, { status: 500 });
  }
}
