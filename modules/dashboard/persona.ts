import type { MembershipRole } from "@prisma/client";

export type DashboardPersona =
  | "founder"
  | "sales_leader"
  | "manager"
  | "employee"
  | "finance"
  | "hr";

export function resolveDashboardPersona(
  role: MembershipRole | string | null | undefined,
): DashboardPersona {
  switch (role) {
    case "SUPER_ADMIN":
    case "ADMIN":
      return "founder";
    case "SALES":
      return "sales_leader";
    case "MANAGER":
    case "DEPARTMENT_HEAD":
      return "manager";
    case "FINANCE":
      return "finance";
    case "HR":
      return "hr";
    case "EMPLOYEE":
    case "OPERATIONS":
    case "CREATIVE":
    case "VIEWER":
    default:
      return "employee";
  }
}

export function personaLabel(persona: DashboardPersona): string {
  switch (persona) {
    case "founder":
      return "Founder overview";
    case "sales_leader":
      return "Sales leadership";
    case "manager":
      return "Manager cockpit";
    case "finance":
      return "Finance control";
    case "hr":
      return "People operations";
    case "employee":
      return "My workspace";
  }
}
