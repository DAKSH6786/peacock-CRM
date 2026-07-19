import "dotenv/config";

import { PrismaClient, MembershipRole } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const adminEmail = (
    process.env.SEED_ADMIN_EMAIL ?? "admin@digitalpeacock.local"
  ).toLowerCase();
  const adminPassword = process.env.SEED_ADMIN_PASSWORD ?? "ChangeMeNow!123";

  const organization = await prisma.organization.upsert({
    where: { slug: "digital-peacock" },
    update: {
      name: "Digital Peacock",
      timezone: "Asia/Kolkata",
      currency: "INR",
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

  const departments = [
    { name: "Leadership", code: "LDR" },
    { name: "Sales", code: "SAL" },
    { name: "Operations", code: "OPS" },
    { name: "Creative", code: "CRV" },
    { name: "HR", code: "HR" },
    { name: "Finance", code: "FIN" },
  ];

  for (const department of departments) {
    await prisma.department.upsert({
      where: {
        organizationId_code: {
          organizationId: organization.id,
          code: department.code,
        },
      },
      update: {
        name: department.name,
        deletedAt: null,
      },
      create: {
        organizationId: organization.id,
        name: department.name,
        code: department.code,
      },
    });
  }

  const leadership = await prisma.department.findUniqueOrThrow({
    where: {
      organizationId_code: {
        organizationId: organization.id,
        code: "LDR",
      },
    },
  });

  const passwordHash = await bcrypt.hash(adminPassword, 12);

  const admin = await prisma.user.upsert({
    where: { email: adminEmail },
    update: {
      name: "Peacock Admin",
      passwordHash,
      status: "ACTIVE",
      organizationId: organization.id,
      departmentId: leadership.id,
      jobTitle: "Administrator",
      deletedAt: null,
    },
    create: {
      email: adminEmail,
      name: "Peacock Admin",
      passwordHash,
      status: "ACTIVE",
      organizationId: organization.id,
      departmentId: leadership.id,
      jobTitle: "Administrator",
    },
  });

  await prisma.membership.upsert({
    where: {
      organizationId_userId: {
        organizationId: organization.id,
        userId: admin.id,
      },
    },
    update: {
      role: MembershipRole.SUPER_ADMIN,
      deletedAt: null,
    },
    create: {
      organizationId: organization.id,
      userId: admin.id,
      role: MembershipRole.SUPER_ADMIN,
    },
  });

  await prisma.auditLog.create({
    data: {
      organizationId: organization.id,
      actorId: admin.id,
      action: "CREATE",
      entityType: "Seed",
      entityId: organization.id,
      metadata: {
        message: "Initial Digital Peacock organization seeded",
      },
    },
  });

  console.log("Seed complete");
  console.log(`  Organization: ${organization.name} (${organization.slug})`);
  console.log(`  Admin email:  ${adminEmail}`);
  console.log(`  Admin password: (from SEED_ADMIN_PASSWORD)`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
