import type { MembershipRole } from "@prisma/client";

export type Permission =
  | "dashboard:view"
  | "crm:view"
  | "crm:manage"
  | "sales:view"
  | "sales:manage"
  | "projects:view"
  | "projects:manage"
  | "employees:view"
  | "employees:manage"
  | "employees:view_compensation"
  | "hr:view"
  | "hr:manage"
  | "finance:view"
  | "finance:manage"
  | "finance:view_profitability"
  | "xyme:view"
  | "xyme:manage"
  | "reports:view"
  | "reports:export"
  | "imports:run"
  | "documents:view"
  | "documents:manage"
  | "approvals:view"
  | "approvals:decide"
  | "settings:view"
  | "settings:manage"
  | "audit:view"
  | "notifications:view";

export type SessionUser = {
  id: string;
  email: string;
  name?: string | null;
  organizationId: string | null;
  role: MembershipRole | null;
  status: string;
};

const ALL_PERMISSIONS: Permission[] = [
  "dashboard:view",
  "crm:view",
  "crm:manage",
  "sales:view",
  "sales:manage",
  "projects:view",
  "projects:manage",
  "employees:view",
  "employees:manage",
  "employees:view_compensation",
  "hr:view",
  "hr:manage",
  "finance:view",
  "finance:manage",
  "finance:view_profitability",
  "xyme:view",
  "xyme:manage",
  "reports:view",
  "reports:export",
  "imports:run",
  "documents:view",
  "documents:manage",
  "approvals:view",
  "approvals:decide",
  "settings:view",
  "settings:manage",
  "audit:view",
  "notifications:view",
];

const ROLE_PERMISSIONS: Record<MembershipRole, Permission[]> = {
  SUPER_ADMIN: ALL_PERMISSIONS,
  ADMIN: ALL_PERMISSIONS.filter((p) => p !== "employees:view_compensation"),
  DEPARTMENT_HEAD: [
    "dashboard:view",
    "crm:view",
    "sales:view",
    "projects:view",
    "projects:manage",
    "employees:view",
    "hr:view",
    "xyme:view",
    "xyme:manage",
    "reports:view",
    "imports:run",
    "documents:view",
    "approvals:view",
    "approvals:decide",
    "notifications:view",
  ],
  MANAGER: [
    "dashboard:view",
    "crm:view",
    "sales:view",
    "projects:view",
    "projects:manage",
    "employees:view",
    "xyme:view",
    "xyme:manage",
    "reports:view",
    "imports:run",
    "documents:view",
    "approvals:view",
    "approvals:decide",
    "notifications:view",
  ],
  EMPLOYEE: [
    "dashboard:view",
    "projects:view",
    "xyme:view",
    "documents:view",
    "notifications:view",
  ],
  FINANCE: [
    "dashboard:view",
    "finance:view",
    "finance:manage",
    "finance:view_profitability",
    "reports:view",
    "reports:export",
    "imports:run",
    "documents:view",
    "approvals:view",
    "approvals:decide",
    "notifications:view",
  ],
  HR: [
    "dashboard:view",
    "employees:view",
    "employees:manage",
    "employees:view_compensation",
    "hr:view",
    "hr:manage",
    "reports:view",
    "imports:run",
    "documents:view",
    "documents:manage",
    "approvals:view",
    "approvals:decide",
    "notifications:view",
  ],
  SALES: [
    "dashboard:view",
    "crm:view",
    "crm:manage",
    "sales:view",
    "sales:manage",
    "reports:view",
    "imports:run",
    "documents:view",
    "notifications:view",
  ],
  OPERATIONS: [
    "dashboard:view",
    "projects:view",
    "projects:manage",
    "employees:view",
    "reports:view",
    "imports:run",
    "documents:view",
    "notifications:view",
  ],
  CREATIVE: [
    "dashboard:view",
    "projects:view",
    "documents:view",
    "notifications:view",
  ],
  VIEWER: ["dashboard:view", "notifications:view"],
};

export function permissionsForRole(
  role: MembershipRole | null | undefined,
): Permission[] {
  if (!role) return [];
  return ROLE_PERMISSIONS[role] ?? [];
}

export function hasPermission(
  role: MembershipRole | null | undefined,
  permission: Permission,
): boolean {
  return permissionsForRole(role).includes(permission);
}
