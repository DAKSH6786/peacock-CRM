import "server-only";

import type { MembershipRole } from "@prisma/client";

import { ForbiddenError, type SessionUser } from "@/permissions";
import { hasPermission } from "@/permissions/types";

import { BaseRepository, type DbClient } from "@/database/repositories/base";

/**
 * Sensitive compensation / bank / tax access. Requires employees:view_compensation.
 */
export class CompensationRepository extends BaseRepository {
  constructor(db?: DbClient) {
    super(db);
  }

  private assertCompensationAccess(user: SessionUser) {
    if (
      !hasPermission(
        user.role as MembershipRole | null,
        "employees:view_compensation",
      )
    ) {
      throw new ForbiddenError(
        "Missing permission: employees:view_compensation",
      );
    }
  }

  getEmployeeCompensation(user: SessionUser, employeeId: string) {
    this.assertCompensationAccess(user);
    if (!user.organizationId) {
      throw new ForbiddenError("User is not assigned to an organization");
    }

    return this.db.employeeCompensation.findFirst({
      where: {
        employeeId,
        organizationId: user.organizationId,
        deletedAt: null,
      },
    });
  }

  getBankDetail(user: SessionUser, employeeId: string) {
    this.assertCompensationAccess(user);
    if (!user.organizationId) {
      throw new ForbiddenError("User is not assigned to an organization");
    }

    return this.db.employeeBankDetail.findFirst({
      where: {
        employeeId,
        organizationId: user.organizationId,
        deletedAt: null,
      },
    });
  }

  getTaxInformation(user: SessionUser, employeeId: string) {
    this.assertCompensationAccess(user);
    if (!user.organizationId) {
      throw new ForbiddenError("User is not assigned to an organization");
    }

    return this.db.employeeTaxInformation.findFirst({
      where: {
        employeeId,
        organizationId: user.organizationId,
        deletedAt: null,
      },
    });
  }
}
