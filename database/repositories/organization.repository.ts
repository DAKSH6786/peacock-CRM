import "server-only";

import { BaseRepository, type DbClient } from "@/database/repositories/base";

export class OrganizationRepository extends BaseRepository {
  constructor(db?: DbClient) {
    super(db);
  }

  findBySlug(slug: string) {
    return this.db.organization.findFirst({
      where: { slug, deletedAt: null },
      include: { settings: true },
    });
  }

  findById(id: string) {
    return this.db.organization.findFirst({
      where: { id, deletedAt: null },
      include: { settings: true },
    });
  }
}
