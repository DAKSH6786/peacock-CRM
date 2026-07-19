import "server-only";

import type { Prisma, PrismaClient } from "@prisma/client";

import { prisma } from "@/database/client";

export type DbClient = PrismaClient | Prisma.TransactionClient;

export type SoftDeleteWhere = {
  deletedAt?: null | Date | { not: null };
};

/**
 * Base repository helpers for org-scoped, soft-deletable entities.
 */
export abstract class BaseRepository {
  constructor(protected readonly db: DbClient = prisma) {}

  protected orgScope(organizationId: string) {
    return { organizationId } as const;
  }

  protected notDeleted() {
    return { deletedAt: null } as const;
  }
}
