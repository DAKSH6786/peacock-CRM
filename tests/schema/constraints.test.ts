import "dotenv/config";

import { PrismaClient } from "@prisma/client";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

const prisma = new PrismaClient();

describe("schema constraints", () => {
  let organizationId: string;

  beforeAll(async () => {
    const org = await prisma.organization.findUnique({
      where: { slug: "digital-peacock" },
    });
    if (!org) {
      throw new Error(
        "Seed data missing — run `npm run db:seed` before schema tests",
      );
    }
    organizationId = org.id;
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  it("enforces unique organization slug", async () => {
    await expect(
      prisma.organization.create({
        data: {
          name: "Duplicate",
          slug: "digital-peacock",
        },
      }),
    ).rejects.toMatchObject({ code: "P2002" });
  });

  it("enforces unique employee code per organization", async () => {
    const admin = await prisma.employee.findFirst({
      where: { organizationId, employeeCode: "DP0001" },
    });
    expect(admin).toBeTruthy();

    await expect(
      prisma.employee.create({
        data: {
          organizationId,
          userId: "nonexistent-user",
          employeeCode: "DP0001",
          officialEmail: "dup@example.com",
          joiningDate: new Date("2026-01-01"),
        },
      }),
    ).rejects.toBeTruthy();
  });

  it("stores money fields as integers (minor units)", async () => {
    const deal = await prisma.deal.create({
      data: {
        organizationId,
        name: "Constraint test deal",
        valueMinor: 125099,
        currencyCode: "INR",
      },
    });
    expect(Number.isInteger(deal.valueMinor)).toBe(true);
    await prisma.deal.delete({ where: { id: deal.id } });
  });

  it("keeps bank details on a separate restricted model", async () => {
    const fields = Object.keys(prisma).filter((k) =>
      ["employee", "employeeBankDetail", "employeeCompensation"].includes(k),
    );
    expect(fields).toEqual(
      expect.arrayContaining([
        "employee",
        "employeeBankDetail",
        "employeeCompensation",
      ]),
    );

    const employeeModelFields = await prisma.$queryRaw<
      Array<{ column_name: string }>
    >`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_name = 'employees'
        AND column_name IN ('accountNumber', 'bankName', 'salary')
    `;
    expect(employeeModelFields).toHaveLength(0);
  });

  it("requires organizationId on leads at the database layer", async () => {
    await expect(
      prisma.$executeRaw`
        INSERT INTO leads (id, "personName", "createdAt", "updatedAt")
        VALUES ('lead_missing_org', 'Test Lead', NOW(), NOW())
      `,
    ).rejects.toBeTruthy();
  });

  it("supports XYME cycle uniqueness per FY quarter", async () => {
    const fy = await prisma.financialYear.findFirstOrThrow({
      where: { organizationId, code: "FY2026-27" },
    });

    const cycle = await prisma.xYMECycle.upsert({
      where: {
        organizationId_financialYearId_quarter: {
          organizationId,
          financialYearId: fy.id,
          quarter: 1,
        },
      },
      update: {},
      create: {
        organizationId,
        financialYearId: fy.id,
        quarter: 1,
        name: "Q1 FY26-27",
        startDate: new Date("2026-04-01"),
        endDate: new Date("2026-06-30"),
        isActive: true,
      },
    });

    await expect(
      prisma.xYMECycle.create({
        data: {
          organizationId,
          financialYearId: fy.id,
          quarter: 1,
          name: "Q1 duplicate",
          startDate: new Date("2026-04-01"),
          endDate: new Date("2026-06-30"),
        },
      }),
    ).rejects.toMatchObject({ code: "P2002" });

    expect(cycle.quarter).toBe(1);
  });
});
