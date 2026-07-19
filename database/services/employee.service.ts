import "server-only";

import { EmployeeRepository } from "@/database/repositories/employee.repository";
import { BaseService } from "@/database/services/base.service";
import type { SessionUser } from "@/permissions";

export class EmployeeService extends BaseService {
  constructor(private readonly employees = new EmployeeRepository()) {
    super();
  }

  list(
    user: SessionUser | null | undefined,
    options?: {
      skip?: number;
      take?: number;
      search?: string;
      departmentId?: string;
    },
  ) {
    const authed = this.requireOrg(this.requirePerm(user, "employees:view"));
    return this.employees.list(authed.organizationId, options);
  }

  getById(user: SessionUser | null | undefined, id: string) {
    const authed = this.requireOrg(this.requirePerm(user, "employees:view"));
    return this.employees.findById(authed.organizationId, id);
  }
}
