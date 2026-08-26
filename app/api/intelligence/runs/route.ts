import { NextResponse } from "next/server";
import { z } from "zod";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  executeAndPersistRun,
  runDemoPipeline,
} from "@/modules/intelligence/service";
import { requirePermission } from "@/permissions";

const bodySchema = z.object({
  propertyId: z.string().min(1).optional(),
  demo: z.boolean().optional(),
  objective: z.string().max(500).optional(),
});

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "intelligence:run");

    const json = await request.json().catch(() => ({}));
    const body = bodySchema.parse(json);

    if (body.demo || !body.propertyId) {
      const result = await runDemoPipeline();
      return NextResponse.json({
        demo: true,
        status: result.status,
        summary: result.summary,
        confidence: result.confidence,
        recommendationCount: result.decide?.recommendations.length ?? 0,
      });
    }

    const { result, runId } = await executeAndPersistRun({
      organizationId: user!.organizationId!,
      propertyId: body.propertyId,
      objective: body.objective,
    });

    return NextResponse.json({
      runId,
      status: result.status,
      summary: result.summary,
      confidence: result.confidence,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to run intelligence";
    const status =
      message === "Unauthorized" || message.includes("Authentication")
        ? 401
        : message.includes("permission") || message === "Forbidden"
          ? 403
          : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
