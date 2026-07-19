import "server-only";

import type { Employee, Prisma } from "@prisma/client";

import { prisma } from "@/database/client";
import { BaseRepository, type DbClient } from "@/database/repositories/base";

/**
 * Ordinary employee queries intentionally omit bank, tax, and compensation joins.
 * Use CompensationRepository for sensitive fields.
 */
export class EmployeeRepository extends BaseRepository {
  constructor(db?: DbClient) {
    super(db);
  }

  findById(organizationId: string, id: string) {
    return this.db.employee.findFirst({
      where: {
        id,
        ...this.orgScope(organizationId),
        ...this.notDeleted(),
      },
      include: {
        department: true,
        team: true,
        jobRole: true,
        designation: true,
        officeLocation: true,
        reportingManager: {
          select: {
            id: true,
            employeeCode: true,
            officialEmail: true,
            user: { select: { id: true, name: true } },
          },
        },
        user: {
          select: { id: true, email: true, name: true, status: true },
        },
      },
    });
  }

  async list(
    organizationId: string,
    options: {
      skip?: number;
      take?: number;
      search?: string;
      departmentId?: string;
    } = {},
  ) {
    const where: Prisma.EmployeeWhereInput = {
      ...this.orgScope(organizationId),
      ...this.notDeleted(),
      ...(options.departmentId ? { departmentId: options.departmentId } : {}),
      ...(options.search
        ? {
            OR: [
              {
                employeeCode: { contains: options.search, mode: "insensitive" },
              },
              {
                officialEmail: {
                  contains: options.search,
                  mode: "insensitive",
                },
              },
              {
                user: {
                  name: { contains: options.search, mode: "insensitive" },
                },
              },
            ],
          }
        : {}),
    };

    const client = this.db === prisma ? prisma : this.db;
    const count = await client.employee.count({ where });
    const rows = await client.employee.findMany({
      where,
      skip: options.skip ?? 0,
      take: options.take ?? 25,
      orderBy: { joiningDate: "desc" },
      select: {
        id: true,
        employeeCode: true,
        officialEmail: true,
        phone: true,
        joiningDate: true,
        employmentType: true,
        employmentStatus: true,
        workMode: true,
        isSalesRole: true,
        departmentId: true,
        teamId: true,
        jobRoleId: true,
        designationId: true,
        reportingManagerId: true,
        officeLocationId: true,
        // Explicitly omit monthlyEmploymentCostMinor, annualCtcMinor
        user: { select: { id: true, name: true, email: true } },
        department: { select: { id: true, name: true, code: true } },
      },
    });
    return [count, rows] as const;
  }

  create(
    organizationId: string,
    data: Omit<Prisma.EmployeeUncheckedCreateInput, "organizationId">,
  ): Promise<Employee> {
    return this.db.employee.create({
      data: { ...data, organizationId },
    });
  }
}
