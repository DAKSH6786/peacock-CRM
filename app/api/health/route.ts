import { NextResponse } from "next/server";

import { prisma } from "@/database";

export const dynamic = "force-dynamic";

export async function GET() {
  const startedAt = Date.now();

  let database: "up" | "down" = "down";
  let databaseError: string | undefined;

  try {
    await prisma.$queryRaw`SELECT 1`;
    database = "up";
  } catch (error) {
    database = "down";
    databaseError =
      error instanceof Error ? error.message : "Unknown database error";
  }

  const status = database === "up" ? "ok" : "degraded";
  const body = {
    status,
    service: "peacock-one",
    version: process.env.npm_package_version ?? "0.1.0",
    timestamp: new Date().toISOString(),
    uptimeMs: Math.round(process.uptime() * 1000),
    checks: {
      database: {
        status: database,
        latencyMs: Date.now() - startedAt,
        ...(databaseError ? { error: databaseError } : {}),
      },
    },
  };

  return NextResponse.json(body, {
    status: status === "ok" ? 200 : 503,
  });
}
