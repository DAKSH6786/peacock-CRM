import type { PrismaClient } from "@prisma/client";

const PERMISSIONS = [
  { code: "dashboard:view", name: "View dashboard", module: "dashboard" },
  { code: "crm:view", name: "View CRM", module: "crm" },
  { code: "crm:manage", name: "Manage CRM", module: "crm" },
  { code: "sales:view", name: "View sales", module: "sales" },
  { code: "sales:manage", name: "Manage sales", module: "sales" },
  { code: "projects:view", name: "View projects", module: "projects" },
  { code: "projects:manage", name: "Manage projects", module: "projects" },
  { code: "employees:view", name: "View employees", module: "employees" },
  { code: "employees:manage", name: "Manage employees", module: "employees" },
  {
    code: "employees:view_compensation",
    name: "View compensation",
    module: "employees",
    isSensitive: true,
  },
  { code: "hr:view", name: "View HR", module: "hr" },
  { code: "hr:manage", name: "Manage HR", module: "hr" },
  { code: "finance:view", name: "View finance", module: "finance" },
  { code: "finance:manage", name: "Manage finance", module: "finance" },
  {
    code: "finance:view_profitability",
    name: "View profitability",
    module: "finance",
    isSensitive: true,
  },
  { code: "xyme:view", name: "View XYME", module: "xyme" },
  { code: "xyme:manage", name: "Manage XYME", module: "xyme" },
  { code: "progress:view", name: "View progress", module: "progress" },
  { code: "progress:manage", name: "Manage progress", module: "progress" },
  { code: "progress:review", name: "Review progress", module: "progress" },
  { code: "reports:view", name: "View reports", module: "reports" },
  { code: "reports:export", name: "Export reports", module: "reports" },
  { code: "documents:view", name: "View documents", module: "documents" },
  { code: "documents:manage", name: "Manage documents", module: "documents" },
  { code: "approvals:view", name: "View approvals", module: "approvals" },
  { code: "approvals:decide", name: "Decide approvals", module: "approvals" },
  { code: "settings:view", name: "View settings", module: "settings" },
  { code: "settings:manage", name: "Manage settings", module: "settings" },
  { code: "audit:view", name: "View audit logs", module: "audit" },
  {
    code: "notifications:view",
    name: "View notifications",
    module: "notifications",
  },
  {
    code: "intelligence:view",
    name: "View generative visibility intelligence",
    module: "intelligence",
  },
  {
    code: "intelligence:manage",
    name: "Manage visibility properties and strategies",
    module: "intelligence",
  },
  {
    code: "intelligence:run",
    name: "Run cognitive intelligence pipelines",
    module: "intelligence",
  },
] as const;

const ROLE_CODES = [
  "SUPER_ADMIN",
  "ADMIN",
  "DEPARTMENT_HEAD",
  "MANAGER",
  "EMPLOYEE",
  "FINANCE",
  "HR",
  "SALES",
  "OPERATIONS",
  "CREATIVE",
  "VIEWER",
] as const;

export async function seedPermissions(
  prisma: PrismaClient,
  organizationId: string,
) {
  for (const permission of PERMISSIONS) {
    await prisma.permission.upsert({
      where: {
        organizationId_code: {
          organizationId,
          code: permission.code,
        },
      },
      update: {
        name: permission.name,
        module: permission.module,
        isSensitive:
          "isSensitive" in permission ? permission.isSensitive : false,
      },
      create: {
        organizationId,
        code: permission.code,
        name: permission.name,
        module: permission.module,
        isSensitive:
          "isSensitive" in permission ? permission.isSensitive : false,
      },
    });
  }

  for (const code of ROLE_CODES) {
    await prisma.role.upsert({
      where: {
        organizationId_code: {
          organizationId,
          code,
        },
      },
      update: {
        name: code.replaceAll("_", " "),
        isSystem: true,
        deletedAt: null,
      },
      create: {
        organizationId,
        code,
        name: code.replaceAll("_", " "),
        isSystem: true,
      },
    });
  }

  const allPermissions = await prisma.permission.findMany({
    where: { organizationId },
  });
  const superAdmin = await prisma.role.findFirstOrThrow({
    where: { organizationId, code: "SUPER_ADMIN" },
  });

  for (const permission of allPermissions) {
    await prisma.rolePermission.upsert({
      where: {
        roleId_permissionId: {
          roleId: superAdmin.id,
          permissionId: permission.id,
        },
      },
      update: {},
      create: {
        roleId: superAdmin.id,
        permissionId: permission.id,
      },
    });
  }
}
