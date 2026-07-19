export type NavItem = {
  href: string;
  label: string;
  permission?: string;
};

export const primaryNav: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", permission: "dashboard:view" },
  { href: "/crm", label: "CRM", permission: "crm:view" },
  { href: "/sales", label: "Sales", permission: "sales:view" },
  { href: "/projects", label: "Projects", permission: "projects:view" },
  { href: "/tasks", label: "Tasks", permission: "projects:view" },
  {
    href: "/company-progress",
    label: "Company progress",
    permission: "reports:view",
  },
  { href: "/departments", label: "Departments", permission: "employees:view" },
  { href: "/employees", label: "Employees", permission: "employees:view" },
  { href: "/xyme", label: "XYME", permission: "xyme:view" },
  { href: "/hr", label: "HR", permission: "hr:view" },
  { href: "/finance", label: "Finance", permission: "finance:view" },
  { href: "/vendors", label: "Vendors", permission: "finance:view" },
  { href: "/reports", label: "Reports", permission: "reports:view" },
  {
    href: "/notifications",
    label: "Notifications",
    permission: "notifications:view",
  },
  { href: "/approvals", label: "Approvals", permission: "approvals:view" },
  { href: "/documents", label: "Documents", permission: "documents:view" },
  { href: "/settings", label: "Settings", permission: "settings:view" },
  { href: "/audit-logs", label: "Audit logs", permission: "audit:view" },
];
