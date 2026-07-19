import "server-only";

import type { MembershipRole } from "@prisma/client";

import { prisma } from "@/database";
import type {
  SearchCategory,
  SearchResponse,
} from "@/modules/search/types";
import type { SessionUser } from "@/permissions";
import { hasPermission, requireOrganization } from "@/permissions";
import type { Permission } from "@/permissions/types";

export type { SearchCategory, SearchHit, SearchResponse } from "@/modules/search/types";

type CategoryConfig = {
  category: SearchCategory;
  permission: Permission;
};

const CATEGORIES: CategoryConfig[] = [
  { category: "Leads", permission: "crm:view" },
  { category: "Contacts", permission: "crm:view" },
  { category: "Companies", permission: "crm:view" },
  { category: "Deals", permission: "crm:view" },
  { category: "Projects", permission: "projects:view" },
  { category: "Tasks", permission: "projects:view" },
  { category: "Employees", permission: "employees:view" },
  { category: "Invoices", permission: "finance:view" },
  { category: "Quotes", permission: "finance:view" },
  { category: "Vendors", permission: "finance:view" },
  { category: "Objectives", permission: "reports:view" },
  { category: "Documents", permission: "documents:view" },
];

function can(role: MembershipRole | null, permission: Permission) {
  return hasPermission(role, permission);
}

export async function universalSearch(
  user: SessionUser,
  rawQuery: string,
): Promise<SearchResponse> {
  const authed = requireOrganization(user);
  const query = rawQuery.trim();
  if (query.length < 2) {
    return { query, groups: [] };
  }

  const organizationId = authed.organizationId;
  const role = authed.role as MembershipRole | null;
  const contains = { contains: query, mode: "insensitive" as const };
  const groups: SearchResponse["groups"] = [];

  const jobs: Array<Promise<void>> = [];

  if (can(role, "crm:view")) {
    jobs.push(
      (async () => {
        const [leads, contacts, companies, deals] = await Promise.all([
          prisma.lead.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [
                { personName: contains },
                { companyName: contains },
                { email: contains },
              ],
            },
            take: 5,
            select: {
              id: true,
              personName: true,
              companyName: true,
              email: true,
            },
          }),
          prisma.contact.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [
                { firstName: contains },
                { lastName: contains },
                { email: contains },
              ],
            },
            take: 5,
            select: { id: true, firstName: true, lastName: true, email: true },
          }),
          prisma.clientCompany.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [{ name: contains }, { domain: contains }],
            },
            take: 5,
            select: { id: true, name: true, domain: true },
          }),
          prisma.deal.findMany({
            where: {
              organizationId,
              deletedAt: null,
              name: contains,
            },
            take: 5,
            select: { id: true, name: true, currencyCode: true },
          }),
        ]);

        if (leads.length) {
          groups.push({
            category: "Leads",
            hits: leads.map((lead) => ({
              id: lead.id,
              category: "Leads",
              title: lead.personName,
              subtitle: lead.companyName ?? lead.email ?? undefined,
              href: "/crm/leads",
            })),
          });
        }
        if (contacts.length) {
          groups.push({
            category: "Contacts",
            hits: contacts.map((contact) => ({
              id: contact.id,
              category: "Contacts",
              title: [contact.firstName, contact.lastName]
                .filter(Boolean)
                .join(" "),
              subtitle: contact.email ?? undefined,
              href: "/crm/contacts",
            })),
          });
        }
        if (companies.length) {
          groups.push({
            category: "Companies",
            hits: companies.map((company) => ({
              id: company.id,
              category: "Companies",
              title: company.name,
              subtitle: company.domain ?? undefined,
              href: "/crm/companies",
            })),
          });
        }
        if (deals.length) {
          groups.push({
            category: "Deals",
            hits: deals.map((deal) => ({
              id: deal.id,
              category: "Deals",
              title: deal.name,
              href: "/crm/deals",
            })),
          });
        }
      })(),
    );
  }

  if (can(role, "projects:view")) {
    jobs.push(
      (async () => {
        const [projects, tasks] = await Promise.all([
          prisma.project.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [{ name: contains }, { code: contains }],
            },
            take: 5,
            select: { id: true, name: true, code: true },
          }),
          prisma.task.findMany({
            where: {
              organizationId,
              deletedAt: null,
              title: contains,
            },
            take: 5,
            select: { id: true, title: true, status: true },
          }),
        ]);
        if (projects.length) {
          groups.push({
            category: "Projects",
            hits: projects.map((project) => ({
              id: project.id,
              category: "Projects",
              title: project.name,
              subtitle: project.code,
              href: "/projects",
            })),
          });
        }
        if (tasks.length) {
          groups.push({
            category: "Tasks",
            hits: tasks.map((task) => ({
              id: task.id,
              category: "Tasks",
              title: task.title,
              subtitle: task.status,
              href: "/tasks",
            })),
          });
        }
      })(),
    );
  }

  if (can(role, "employees:view")) {
    jobs.push(
      (async () => {
        const employees = await prisma.employee.findMany({
          where: {
            organizationId,
            deletedAt: null,
            OR: [
              { employeeCode: contains },
              { officialEmail: contains },
              { user: { name: contains } },
            ],
          },
          take: 5,
          select: {
            id: true,
            employeeCode: true,
            officialEmail: true,
            user: { select: { name: true } },
            // Never select compensation / bank fields
          },
        });
        if (employees.length) {
          groups.push({
            category: "Employees",
            hits: employees.map((employee) => ({
              id: employee.id,
              category: "Employees",
              title: employee.user?.name ?? employee.employeeCode,
              subtitle: employee.employeeCode,
              href: `/employees/${employee.id}`,
            })),
          });
        }
      })(),
    );
  }

  if (can(role, "finance:view")) {
    jobs.push(
      (async () => {
        const [invoices, quotes, vendors] = await Promise.all([
          prisma.invoice.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [
                { invoiceNumber: contains },
                { draftNumber: contains },
              ],
            },
            take: 5,
            select: {
              id: true,
              invoiceNumber: true,
              draftNumber: true,
              status: true,
            },
          }),
          prisma.quote.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [{ quoteNumber: contains }, { draftNumber: contains }],
            },
            take: 5,
            select: {
              id: true,
              quoteNumber: true,
              draftNumber: true,
              status: true,
            },
          }),
          prisma.vendor.findMany({
            where: {
              organizationId,
              deletedAt: null,
              OR: [{ name: contains }, { code: contains }],
            },
            take: 5,
            select: { id: true, name: true, code: true },
          }),
        ]);
        if (invoices.length) {
          groups.push({
            category: "Invoices",
            hits: invoices.map((invoice) => ({
              id: invoice.id,
              category: "Invoices",
              title: invoice.invoiceNumber ?? invoice.draftNumber ?? invoice.id,
              subtitle: invoice.status,
              href: "/finance/invoices",
            })),
          });
        }
        if (quotes.length) {
          groups.push({
            category: "Quotes",
            hits: quotes.map((quote) => ({
              id: quote.id,
              category: "Quotes",
              title: quote.quoteNumber ?? quote.draftNumber ?? quote.id,
              subtitle: quote.status,
              href: "/finance/quotes",
            })),
          });
        }
        if (vendors.length) {
          groups.push({
            category: "Vendors",
            hits: vendors.map((vendor) => ({
              id: vendor.id,
              category: "Vendors",
              title: vendor.name,
              subtitle: vendor.code ?? undefined,
              href: "/vendors",
            })),
          });
        }
      })(),
    );
  }

  if (can(role, "reports:view")) {
    jobs.push(
      (async () => {
        const objectives = await prisma.objective.findMany({
          where: {
            organizationId,
            deletedAt: null,
            title: contains,
          },
          take: 5,
          select: { id: true, title: true, progressPct: true },
        });
        if (objectives.length) {
          groups.push({
            category: "Objectives",
            hits: objectives.map((objective) => ({
              id: objective.id,
              category: "Objectives",
              title: objective.title,
              subtitle: `${objective.progressPct}%`,
              href: "/company-progress",
            })),
          });
        }
      })(),
    );
  }

  if (can(role, "documents:view")) {
    jobs.push(
      (async () => {
        // Only surface the current user's documents unless HR/admin
        const isHr =
          can(role, "hr:view") || can(role, "employees:manage");
        const employee = await prisma.employee.findFirst({
          where: { userId: authed.id, organizationId, deletedAt: null },
          select: { id: true },
        });
        const documents = await prisma.employeeDocument.findMany({
          where: {
            organizationId,
            deletedAt: null,
            title: contains,
            ...(isHr || !employee ? {} : { employeeId: employee.id }),
          },
          take: 5,
          select: { id: true, title: true },
        });
        if (documents.length) {
          groups.push({
            category: "Documents",
            hits: documents.map((doc) => ({
              id: doc.id,
              category: "Documents",
              title: doc.title,
              href: "/documents",
            })),
          });
        }
      })(),
    );
  }

  await Promise.all(jobs);

  // Stable category order
  const order = new Map(CATEGORIES.map((c, i) => [c.category, i]));
  groups.sort(
    (a, b) => (order.get(a.category) ?? 99) - (order.get(b.category) ?? 99),
  );

  return { query, groups };
}
