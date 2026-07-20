import type { PrismaClient } from "@prisma/client";

const DEPARTMENTS = [
  { name: "Leadership", code: "LDR" },
  { name: "Sales", code: "SAL" },
  { name: "Operations", code: "OPS" },
  { name: "Creative", code: "CRV" },
  { name: "HR", code: "HR" },
  { name: "Finance", code: "FIN" },
] as const;

export async function seedDepartments(
  prisma: PrismaClient,
  organizationId: string,
) {
  const created: Record<string, { id: string; code: string; name: string }> =
    {};

  for (const department of DEPARTMENTS) {
    const row = await prisma.department.upsert({
      where: {
        organizationId_code: {
          organizationId,
          code: department.code,
        },
      },
      update: {
        name: department.name,
        deletedAt: null,
      },
      create: {
        organizationId,
        name: department.name,
        code: department.code,
      },
    });
    created[department.code] = row;
  }

  return {
    leadership: created.LDR!,
    sales: created.SAL!,
    operations: created.OPS!,
    creative: created.CRV!,
    hr: created.HR!,
    finance: created.FIN!,
  };
}
