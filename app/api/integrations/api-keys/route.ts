import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import { API_KEY_SCOPES } from "@/modules/integrations";
import {
  createOrganizationApiKey,
  revokeOrganizationApiKey,
} from "@/modules/integrations/service";
import { requirePermission } from "@/permissions";
import { prisma } from "@/database";
import type { ApiKeyScope } from "@/modules/integrations";

export async function GET() {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "settings:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const keys = await prisma.apiKey.findMany({
      where: { organizationId: user.organizationId },
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        name: true,
        keyPrefix: true,
        scopes: true,
        expiresAt: true,
        revokedAt: true,
        lastUsedAt: true,
        createdAt: true,
      },
    });

    return NextResponse.json({ keys, scopes: API_KEY_SCOPES });
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
      action?: "create" | "revoke";
      name?: string;
      scopes?: ApiKeyScope[];
      expiresAt?: string | null;
      apiKeyId?: string;
    };

    if (body.action === "revoke" && body.apiKeyId) {
      const ok = await revokeOrganizationApiKey({
        user,
        organizationId: user.organizationId,
        apiKeyId: body.apiKeyId,
      });
      return NextResponse.json({ ok });
    }

    if (!body.name || !body.scopes?.length) {
      return NextResponse.json({ error: "name and scopes required" }, { status: 400 });
    }

    const result = await createOrganizationApiKey({
      user,
      organizationId: user.organizationId,
      name: body.name,
      scopes: body.scopes,
      expiresAt: body.expiresAt ? new Date(body.expiresAt) : null,
    });

    return NextResponse.json({
      key: {
        id: result.record.id,
        name: result.record.name,
        keyPrefix: result.record.keyPrefix,
        scopes: result.record.scopes,
      },
      // Shown once — never stored in plaintext
      secret: result.secret,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
