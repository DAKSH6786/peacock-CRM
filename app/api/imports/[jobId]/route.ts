import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { createObjectStorage } from "@/lib/storage";
import { prisma } from "@/database";
import { canImportEntity } from "@/modules/imports";

type Params = { params: Promise<{ jobId: string }> };

export async function GET(_request: Request, { params }: Params) {
  const session = await auth();
  const user = toSessionUser(session);
  if (!user?.organizationId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { jobId } = await params;
  const job = await prisma.importJob.findFirst({
    where: { id: jobId, organizationId: user.organizationId },
    include: { createdBy: { select: { id: true, name: true, email: true } } },
  });

  if (!job) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  if (!canImportEntity(user, job.entityType)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  return NextResponse.json({ job });
}

export async function POST(request: Request, { params }: Params) {
  const session = await auth();
  const user = toSessionUser(session);
  if (!user?.organizationId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { jobId } = await params;
  const body = (await request.json()) as { action?: string };
  const job = await prisma.importJob.findFirst({
    where: { id: jobId, organizationId: user.organizationId },
  });

  if (!job) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  if (!canImportEntity(user, job.entityType)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  if (body.action === "error-file") {
    if (!job.errorFileKey) {
      return NextResponse.json({ error: "No error file" }, { status: 404 });
    }
    const storage = createObjectStorage();
    const url = await storage.getSignedDownloadUrl(job.errorFileKey, {
      expiresInSeconds: 600,
    });
    try {
      const buffer = await storage.getObject(job.errorFileKey);
      return new NextResponse(new Uint8Array(buffer), {
        headers: {
          "content-type": "text/csv",
          "content-disposition": `attachment; filename="import-${job.id}-errors.csv"`,
        },
      });
    } catch {
      return NextResponse.json({ url });
    }
  }

  return NextResponse.json({ error: "Unknown action" }, { status: 400 });
}
