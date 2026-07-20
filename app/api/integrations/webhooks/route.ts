import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { createWebhookEndpoint } from "@/modules/integrations/service";
import { requirePermission } from "@/permissions";
import { prisma } from "@/database";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "settings:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const endpoints = await prisma.webhookEndpoint.findMany({
      where: { organizationId: user.organizationId, deletedAt: null },
      include: {
        deliveries: {
          orderBy: { createdAt: "desc" },
          take: 10,
        },
      },
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json({ endpoints });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "settings:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = (await request.json()) as {
      name: string;
      url: string;
      events: string[];
    };

    if (!body.name || !body.url || !body.events?.length) {
      return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
    }

    const result = await createWebhookEndpoint({
      user,
      organizationId: user.organizationId,
      name: body.name,
      url: body.url,
      events: body.events,
    });

    return NextResponse.json({
      endpoint: result.endpoint,
      // Shown once
      signingSecret: result.signingSecret,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
