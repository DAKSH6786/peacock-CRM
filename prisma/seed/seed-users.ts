import type { PrismaClient } from "@prisma/client";
import { MembershipRole } from "@prisma/client";
import bcrypt from "bcryptjs";

export async function seedAdminUser(
  prisma: PrismaClient,
  input: { organizationId: string; departmentId: string },
) {
  const adminEmail = (
    process.env.SEED_ADMIN_EMAIL ?? "admin@digitalpeacock.local"
  ).toLowerCase();
  const adminPassword = process.env.SEED_ADMIN_PASSWORD ?? "ChangeMeNow!123";
  const passwordHash = await bcrypt.hash(adminPassword, 12);

  const office = await prisma.officeLocation.findFirst({
    where: { organizationId: input.organizationId, code: "HQ" },
  });

  const admin = await prisma.user.upsert({
    where: { email: adminEmail },
    update: {
      name: "Peacock Admin",
      passwordHash,
      status: "ACTIVE",
      organizationId: input.organizationId,
      departmentId: input.departmentId,
      jobTitle: "Administrator",
      deletedAt: null,
    },
    create: {
      email: adminEmail,
      name: "Peacock Admin",
      passwordHash,
      status: "ACTIVE",
      organizationId: input.organizationId,
      departmentId: input.departmentId,
      jobTitle: "Administrator",
    },
  });

  await prisma.userProfile.upsert({
    where: { userId: admin.id },
    update: {
      displayName: "Peacock Admin",
      organizationId: input.organizationId,
      deletedAt: null,
    },
    create: {
      organizationId: input.organizationId,
      userId: admin.id,
      displayName: "Peacock Admin",
    },
  });

  await prisma.membership.upsert({
    where: {
      organizationId_userId: {
        organizationId: input.organizationId,
        userId: admin.id,
      },
    },
    update: {
      role: MembershipRole.SUPER_ADMIN,
      deletedAt: null,
    },
    create: {
      organizationId: input.organizationId,
      userId: admin.id,
      role: MembershipRole.SUPER_ADMIN,
    },
  });

  const superAdminRole = await prisma.role.findFirstOrThrow({
    where: { organizationId: input.organizationId, code: "SUPER_ADMIN" },
  });

  await prisma.userRole.upsert({
    where: {
      userId_roleId: {
        userId: admin.id,
        roleId: superAdminRole.id,
      },
    },
    update: { deletedAt: null, organizationId: input.organizationId },
    create: {
      organizationId: input.organizationId,
      userId: admin.id,
      roleId: superAdminRole.id,
    },
  });

  await prisma.employee.upsert({
    where: { userId: admin.id },
    update: {
      organizationId: input.organizationId,
      employeeCode: "DP0001",
      officialEmail: adminEmail,
      joiningDate: new Date("2020-01-01"),
      employmentType: "FULL_TIME",
      employmentStatus: "ACTIVE",
      departmentId: input.departmentId,
      officeLocationId: office?.id,
      workMode: "HYBRID",
      deletedAt: null,
    },
    create: {
      organizationId: input.organizationId,
      userId: admin.id,
      employeeCode: "DP0001",
      officialEmail: adminEmail,
      joiningDate: new Date("2020-01-01"),
      employmentType: "FULL_TIME",
      employmentStatus: "ACTIVE",
      departmentId: input.departmentId,
      officeLocationId: office?.id,
      workMode: "HYBRID",
    },
  });

  return admin;
}
