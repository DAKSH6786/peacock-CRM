"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

const LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  crm: "CRM",
  leads: "Leads",
  companies: "Companies",
  contacts: "Contacts",
  deals: "Deals",
  pipeline: "Pipeline",
  sales: "Sales",
  projects: "Projects",
  deliverables: "Deliverables",
  tasks: "Tasks",
  timesheets: "Timesheets",
  resources: "Resources",
  "company-progress": "Company Progress",
  departments: "Department Progress",
  xyme: "XYME",
  employees: "Employees",
  hr: "People",
  attendance: "Attendance",
  leaves: "Leave",
  recruitment: "Recruitment",
  onboarding: "Onboarding",
  assets: "Assets",
  policies: "Policies",
  finance: "Finance",
  quotes: "Quotes",
  invoices: "Invoices",
  payments: "Payments",
  expenses: "Expenses",
  vendors: "Vendors",
  reports: "Reports",
  saved: "Saved Reports",
  exports: "Exports",
  settings: "Settings",
  users: "Users and Roles",
  integrations: "Integrations",
  "audit-logs": "Audit Logs",
  approvals: "Approvals",
  notifications: "Notifications",
  "my-work": "My Work",
  documents: "Documents",
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) return null;

  const crumbs = segments.map((segment, index) => {
    const href = `/${segments.slice(0, index + 1).join("/")}`;
    return {
      href,
      label: LABELS[segment] ?? segment.replace(/-/g, " "),
    };
  });

  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-[var(--muted)]">
        <li>
          <Link
            href="/dashboard"
            className="rounded hover:text-[var(--foreground)] focus-visible:outline-none"
          >
            Home
          </Link>
        </li>
        {crumbs.map((crumb, index) => (
          <li key={crumb.href} className="flex items-center gap-1">
            <ChevronRight className="h-3.5 w-3.5" aria-hidden />
            {index === crumbs.length - 1 ? (
              <span
                className="font-medium text-[var(--foreground)]"
                aria-current="page"
              >
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="rounded hover:text-[var(--foreground)]"
              >
                {crumb.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
