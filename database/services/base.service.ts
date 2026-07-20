import "server-only";

import type { Prisma } from "@prisma/client";

import { prisma } from "@/database/client";
import { createAuditLog } from "@/modules/audit/service";
import type { SessionUser } from "@/permissions";
import { requireOrganization, requirePermission } from "@/permissions";
import type { Permission } from "@/permissions/types";
import type { AuditAction } from "@prisma/client";

export abstract class BaseService {
  protected requireOrg(user: SessionUser | null | undefined) {
    return requireOrganization(user);
  }

  protected requirePerm(
    user: SessionUser | null | undefined,
    permission: Permission,
  ) {
    return requirePermission(user, permission);
  }

  protected async withTransaction<T>(
    fn: (tx: Prisma.TransactionClient) => Promise<T>,
  ): Promise<T> {
    return prisma.$transaction(fn);
  }

  protected async audit(input: {
    organizationId: string;
    actorId?: string | null;
    action: AuditAction;
    entityType: string;
    entityId?: string | null;
    metadata?: Prisma.InputJsonValue;
  }) {
    return createAuditLog(input);
  }
}
