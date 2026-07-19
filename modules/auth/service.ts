import "server-only";

import bcrypt from "bcryptjs";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";

export async function verifyCredentials(email: string, password: string) {
  const user = await prisma.user.findFirst({
    where: {
      email: email.toLowerCase(),
      deletedAt: null,
      status: { in: ["ACTIVE", "INVITED"] },
    },
    include: {
      memberships: {
        where: { deletedAt: null },
        take: 1,
        orderBy: { createdAt: "asc" },
      },
    },
  });

  if (!user?.passwordHash) {
    return null;
  }

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    if (user.organizationId) {
      await createAuditLog({
        organizationId: user.organizationId,
        actorId: user.id,
        action: "LOGIN_FAILED",
        entityType: "User",
        entityId: user.id,
        metadata: { email: user.email },
      });
    }
    return null;
  }

  const membership = user.memberships[0] ?? null;

  return {
    id: user.id,
    email: user.email,
    name: user.name,
    organizationId: user.organizationId,
    role: membership?.role ?? null,
    status: user.status,
  };
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 12);
}
