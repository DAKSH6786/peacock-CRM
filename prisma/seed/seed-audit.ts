import type { PrismaClient } from "@prisma/client";

export async function seedAudit(
  prisma: PrismaClient,
  input: { organizationId: string; actorId: string },
) {
  await prisma.auditLog.create({
    data: {
      organizationId: input.organizationId,
      actorId: input.actorId,
      action: "CREATE",
      entityType: "Seed",
      entityId: input.organizationId,
      metadata: {
        message: "Digital Peacock organization bootstrap seed completed",
      },
    },
  });
}
