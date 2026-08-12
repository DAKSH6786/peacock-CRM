import type { Permission } from "@/permissions/types";

export type NavLink = {
  href: string;
  label: string;
  permission?: Permission;
};

export type NavSection = {
  id: string;
  label: string;
  items: NavLink[];
};

export const navigationSections: NavSection[] = [
  {
    id: "home",
    label: "Home",
    items: [
      { href: "/dashboard", label: "Dashboard", permission: "dashboard:view" },
      { href: "/my-work", label: "My Work", permission: "dashboard:view" },
      { href: "/approvals", label: "Approvals", permission: "approvals:view" },
      {
        href: "/notifications",
        label: "Notifications",
        permission: "notifications:view",
      },
    ],
  },
  {
    id: "growth",
    label: "Growth",
    items: [
      { href: "/crm", label: "CRM", permission: "crm:view" },
      { href: "/crm/leads", label: "Leads", permission: "crm:view" },
      { href: "/crm/pipeline", label: "Pipeline", permission: "crm:view" },
      { href: "/crm/follow-ups", label: "Follow-ups", permission: "crm:view" },
      { href: "/crm/workload", label: "Workload", permission: "crm:view" },
      { href: "/crm/companies", label: "Companies", permission: "crm:view" },
      { href: "/crm/contacts", label: "Contacts", permission: "crm:view" },
      { href: "/crm/deals", label: "Deals", permission: "crm:view" },
      { href: "/sales", label: "Sales", permission: "sales:view" },
    ],
  },
  {
    id: "delivery",
    label: "Delivery",
    items: [
      { href: "/projects", label: "Projects", permission: "projects:view" },
      {
        href: "/deliverables",
        label: "Deliverables",
        permission: "projects:view",
      },
      { href: "/tasks", label: "Tasks", permission: "projects:view" },
      { href: "/timesheets", label: "Timesheets", permission: "projects:view" },
      { href: "/resources", label: "Resources", permission: "projects:view" },
    ],
  },
  {
    id: "performance",
    label: "Performance",
    items: [
      {
        href: "/company-progress",
        label: "Company Progress",
        permission: "progress:view",
      },
      {
        href: "/company-progress/objectives",
        label: "Objectives",
        permission: "progress:view",
      },
      {
        href: "/company-progress/scorecards",
        label: "Scorecards",
        permission: "progress:view",
      },
      {
        href: "/company-progress/reviews",
        label: "Business Reviews",
        permission: "progress:view",
      },
      {
        href: "/departments",
        label: "Department Progress",
        permission: "progress:view",
      },
      { href: "/xyme", label: "XYME", permission: "xyme:view" },
      { href: "/employees", label: "Employees", permission: "employees:view" },
    ],
  },
  {
    id: "people",
    label: "People",
    items: [
      {
        href: "/employees",
        label: "Employee Directory",
        permission: "employees:view",
      },
      { href: "/hr/attendance", label: "Attendance", permission: "hr:view" },
      { href: "/hr/leaves", label: "Leave", permission: "hr:view" },
      { href: "/hr/recruitment", label: "Recruitment", permission: "hr:view" },
      { href: "/hr/onboarding", label: "Onboarding", permission: "hr:view" },
      { href: "/hr/assets", label: "Assets", permission: "hr:view" },
      { href: "/hr/policies", label: "Policies", permission: "hr:view" },
    ],
  },
  {
    id: "finance",
    label: "Finance",
    items: [
      { href: "/finance/quotes", label: "Quotes", permission: "finance:view" },
      {
        href: "/finance/invoices",
        label: "Invoices",
        permission: "finance:view",
      },
      {
        href: "/finance/payments",
        label: "Payments",
        permission: "finance:view",
      },
      {
        href: "/finance/expenses",
        label: "Expenses",
        permission: "finance:view",
      },
      { href: "/vendors", label: "Vendors", permission: "finance:view" },
    ],
  },
  {
    id: "visibility",
    label: "Visibility Intelligence",
    items: [
      {
        href: "/intelligence",
        label: "Cockpit",
        permission: "intelligence:view",
      },
      {
        href: "/intelligence/properties",
        label: "Properties",
        permission: "intelligence:view",
      },
      {
        href: "/intelligence/visibility",
        label: "AI Visibility",
        permission: "intelligence:view",
      },
      {
        href: "/intelligence/strategy",
        label: "90-Day Strategy",
        permission: "intelligence:view",
      },
      {
        href: "/intelligence/recommendations",
        label: "Recommendations",
        permission: "intelligence:view",
      },
    ],
  },
  {
    id: "intelligence",
    label: "Business Intelligence",
    items: [
      { href: "/reports", label: "Reports", permission: "reports:view" },
      {
        href: "/reports/builder",
        label: "Report builder",
        permission: "reports:view",
      },
      {
        href: "/reports/saved",
        label: "Saved Reports",
        permission: "reports:view",
      },
      { href: "/exports", label: "Exports", permission: "reports:view" },
      { href: "/imports", label: "Imports", permission: "imports:run" },
      { href: "/documents", label: "Documents", permission: "documents:view" },
    ],
  },
  {
    id: "administration",
    label: "Administration",
    items: [
      { href: "/settings", label: "Settings", permission: "settings:view" },
      {
        href: "/settings/users",
        label: "Users and Roles",
        permission: "settings:manage",
      },
      {
        href: "/settings/integrations",
        label: "Integrations",
        permission: "settings:manage",
      },
      { href: "/audit-logs", label: "Audit Logs", permission: "audit:view" },
    ],
  },
];

export const quickCreateItems: NavLink[] = [
  { href: "/crm/leads?create=1", label: "Lead", permission: "crm:manage" },
  {
    href: "/projects?create=1",
    label: "Project",
    permission: "projects:manage",
  },
  { href: "/tasks?create=1", label: "Task", permission: "projects:manage" },
  {
    href: "/finance/invoices?create=1",
    label: "Invoice",
    permission: "finance:manage",
  },
  {
    href: "/hr/leaves?create=1",
    label: "Leave request",
    permission: "hr:view",
  },
];

export function filterNavByRole(
  role: string | null,
  hasPermission: (role: never, permission: Permission) => boolean,
): NavSection[] {
  return navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (!item.permission) return true;
        return hasPermission(role as never, item.permission);
      }),
    }))
    .filter((section) => section.items.length > 0);
}
