import type { PrismaClient } from "@prisma/client";

export async function seedOrganization(prisma: PrismaClient) {
  const organization = await prisma.organization.upsert({
    where: { slug: "digital-peacock" },
    update: {
      name: "Digital Peacock",
      timezone: "Asia/Kolkata",
      currency: "INR",
      locale: "en-IN",
      deletedAt: null,
    },
    create: {
      name: "Digital Peacock",
      slug: "digital-peacock",
      timezone: "Asia/Kolkata",
      currency: "INR",
      locale: "en-IN",
    },
  });

  await prisma.organizationSettings.upsert({
    where: { organizationId: organization.id },
    update: {
      fiscalYearStartMonth: 4,
      invoicePrefix: "DP-INV",
      quotePrefix: "DP-QT",
      employeeCodePrefix: "DP",
    },
    create: {
      organizationId: organization.id,
      fiscalYearStartMonth: 4,
      invoicePrefix: "DP-INV",
      quotePrefix: "DP-QT",
      employeeCodePrefix: "DP",
    },
  });

  const yearStart = new Date("2026-04-01");
  const yearEnd = new Date("2027-03-31");

  await prisma.financialYear.upsert({
    where: {
      organizationId_code: {
        organizationId: organization.id,
        code: "FY2026-27",
      },
    },
    update: {
      name: "FY 2026-27",
      startDate: yearStart,
      endDate: yearEnd,
      isCurrent: true,
      deletedAt: null,
    },
    create: {
      organizationId: organization.id,
      name: "FY 2026-27",
      code: "FY2026-27",
      startDate: yearStart,
      endDate: yearEnd,
      isCurrent: true,
    },
  });

  await prisma.currency.upsert({
    where: {
      organizationId_code: {
        organizationId: organization.id,
        code: "INR",
      },
    },
    update: { isDefault: true, name: "Indian Rupee", symbol: "₹" },
    create: {
      organizationId: organization.id,
      code: "INR",
      name: "Indian Rupee",
      symbol: "₹",
      isDefault: true,
    },
  });

  await prisma.officeLocation.upsert({
    where: {
      organizationId_code: {
        organizationId: organization.id,
        code: "HQ",
      },
    },
    update: {
      name: "Headquarters",
      city: "Bengaluru",
      country: "IN",
      isPrimary: true,
      deletedAt: null,
    },
    create: {
      organizationId: organization.id,
      name: "Headquarters",
      code: "HQ",
      city: "Bengaluru",
      country: "IN",
      isPrimary: true,
      timezone: "Asia/Kolkata",
    },
  });

  return organization;
}
