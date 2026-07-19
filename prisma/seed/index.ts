import "dotenv/config";

import { PrismaClient } from "@prisma/client";

import { seedAudit } from "./seed-audit";
import { seedDepartments } from "./seed-departments";
import { seedOrganization } from "./seed-organization";
import { seedPermissions } from "./seed-permissions";
import { seedAdminUser } from "./seed-users";

const prisma = new PrismaClient();

async function main() {
  console.log("Seeding Peacock One…");

  const organization = await seedOrganization(prisma);
  await seedPermissions(prisma, organization.id);
  const departments = await seedDepartments(prisma, organization.id);
  const admin = await seedAdminUser(prisma, {
    organizationId: organization.id,
    departmentId: departments.leadership.id,
  });
  await seedAudit(prisma, {
    organizationId: organization.id,
    actorId: admin.id,
  });

  console.log("Seed complete");
  console.log(`  Organization: ${organization.name} (${organization.slug})`);
  console.log(`  Admin email:  ${admin.email}`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
