import type { Permission } from "@/permissions/types";

export type ImportEntityType =
  | "employees"
  | "leads"
  | "contacts"
  | "clients"
  | "deals"
  | "attendance"
  | "revenue_attribution"
  | "projects"
  | "invoices"
  | "payments"
  | "expenses"
  | "vendors";

export type DuplicatePolicy = "SKIP" | "UPDATE" | "FAIL";
export type PartialImportPolicy = "COMMIT_VALID" | "ALL_OR_NOTHING";

export type ImportColumnDef = {
  key: string;
  label: string;
  required?: boolean;
  type?: "string" | "email" | "date" | "number" | "boolean";
};

export type ImportEntityDefinition = {
  key: ImportEntityType;
  label: string;
  description: string;
  permission: Permission;
  columns: ImportColumnDef[];
  /** Fields used for duplicate detection within a file / against existing keys */
  uniqueKeys: string[];
};

export const IMPORT_CATALOG: ImportEntityDefinition[] = [
  {
    key: "employees",
    label: "Employees",
    description: "Employee roster and HR profile basics.",
    permission: "employees:manage",
    uniqueKeys: ["employeeCode", "workEmail"],
    columns: [
      { key: "employeeCode", label: "Employee code", required: true },
      { key: "workEmail", label: "Work email", required: true, type: "email" },
      { key: "firstName", label: "First name", required: true },
      { key: "lastName", label: "Last name", required: true },
      { key: "department", label: "Department" },
      { key: "jobTitle", label: "Job title" },
      { key: "startDate", label: "Start date", type: "date" },
    ],
  },
  {
    key: "leads",
    label: "Leads",
    description: "Inbound and outbound CRM leads.",
    permission: "crm:manage",
    uniqueKeys: ["email"],
    columns: [
      { key: "fullName", label: "Full name", required: true },
      { key: "email", label: "Email", required: true, type: "email" },
      { key: "company", label: "Company" },
      { key: "phone", label: "Phone" },
      { key: "source", label: "Source" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "contacts",
    label: "Contacts",
    description: "People linked to client companies.",
    permission: "crm:manage",
    uniqueKeys: ["email"],
    columns: [
      { key: "fullName", label: "Full name", required: true },
      { key: "email", label: "Email", required: true, type: "email" },
      { key: "clientCompany", label: "Client company", required: true },
      { key: "title", label: "Title" },
      { key: "phone", label: "Phone" },
    ],
  },
  {
    key: "clients",
    label: "Client companies",
    description: "Client / account company records.",
    permission: "crm:manage",
    uniqueKeys: ["name"],
    columns: [
      { key: "name", label: "Company name", required: true },
      { key: "industry", label: "Industry" },
      { key: "website", label: "Website" },
      { key: "billingEmail", label: "Billing email", type: "email" },
      { key: "country", label: "Country" },
    ],
  },
  {
    key: "deals",
    label: "Deals",
    description: "Pipeline opportunities.",
    permission: "crm:manage",
    uniqueKeys: ["name", "clientCompany"],
    columns: [
      { key: "name", label: "Deal name", required: true },
      { key: "clientCompany", label: "Client company", required: true },
      { key: "amount", label: "Amount", type: "number" },
      { key: "currency", label: "Currency" },
      { key: "stage", label: "Stage" },
      { key: "closeDate", label: "Close date", type: "date" },
      { key: "ownerEmail", label: "Owner email", type: "email" },
    ],
  },
  {
    key: "attendance",
    label: "Attendance",
    description: "Daily attendance punches / status.",
    permission: "hr:manage",
    uniqueKeys: ["employeeCode", "date"],
    columns: [
      { key: "employeeCode", label: "Employee code", required: true },
      { key: "date", label: "Date", required: true, type: "date" },
      { key: "status", label: "Status", required: true },
      { key: "checkIn", label: "Check in" },
      { key: "checkOut", label: "Check out" },
    ],
  },
  {
    key: "revenue_attribution",
    label: "Revenue attribution",
    description: "Attributed revenue lines for sales economics.",
    permission: "sales:manage",
    uniqueKeys: ["reference"],
    columns: [
      { key: "reference", label: "Reference", required: true },
      { key: "dealName", label: "Deal name" },
      { key: "ownerEmail", label: "Owner email", type: "email" },
      { key: "amount", label: "Amount", required: true, type: "number" },
      { key: "currency", label: "Currency", required: true },
      { key: "recognizedOn", label: "Recognized on", type: "date" },
    ],
  },
  {
    key: "projects",
    label: "Projects",
    description: "Delivery projects and retainers.",
    permission: "projects:manage",
    uniqueKeys: ["code"],
    columns: [
      { key: "code", label: "Project code", required: true },
      { key: "name", label: "Name", required: true },
      { key: "clientCompany", label: "Client company" },
      { key: "status", label: "Status" },
      { key: "startDate", label: "Start date", type: "date" },
      { key: "endDate", label: "End date", type: "date" },
    ],
  },
  {
    key: "invoices",
    label: "Invoices",
    description: "Customer invoices.",
    permission: "finance:manage",
    uniqueKeys: ["invoiceNumber"],
    columns: [
      { key: "invoiceNumber", label: "Invoice number", required: true },
      { key: "clientCompany", label: "Client company", required: true },
      { key: "issueDate", label: "Issue date", required: true, type: "date" },
      { key: "dueDate", label: "Due date", type: "date" },
      { key: "amount", label: "Amount", required: true, type: "number" },
      { key: "currency", label: "Currency", required: true },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "payments",
    label: "Payments",
    description: "Customer payment receipts.",
    permission: "finance:manage",
    uniqueKeys: ["paymentReference"],
    columns: [
      { key: "paymentReference", label: "Payment reference", required: true },
      { key: "invoiceNumber", label: "Invoice number" },
      { key: "amount", label: "Amount", required: true, type: "number" },
      { key: "currency", label: "Currency", required: true },
      { key: "paidOn", label: "Paid on", required: true, type: "date" },
      { key: "method", label: "Method" },
    ],
  },
  {
    key: "expenses",
    label: "Expenses",
    description: "Expense claims and operating costs.",
    permission: "finance:manage",
    uniqueKeys: ["reference"],
    columns: [
      { key: "reference", label: "Reference", required: true },
      { key: "category", label: "Category", required: true },
      { key: "amount", label: "Amount", required: true, type: "number" },
      { key: "currency", label: "Currency", required: true },
      { key: "spentOn", label: "Spent on", required: true, type: "date" },
      { key: "vendor", label: "Vendor" },
      { key: "employeeCode", label: "Employee code" },
    ],
  },
  {
    key: "vendors",
    label: "Vendors",
    description: "Supplier and vendor master data.",
    permission: "finance:manage",
    uniqueKeys: ["name"],
    columns: [
      { key: "name", label: "Vendor name", required: true },
      { key: "email", label: "Email", type: "email" },
      { key: "taxId", label: "Tax ID" },
      { key: "country", label: "Country" },
      { key: "paymentTerms", label: "Payment terms" },
    ],
  },
];

export function getImportDefinition(
  key: string,
): ImportEntityDefinition | undefined {
  return IMPORT_CATALOG.find((item) => item.key === key);
}

export function buildCsvTemplate(definition: ImportEntityDefinition): string {
  const headers = definition.columns.map((c) => c.key);
  return `${headers.join(",")}\n`;
}
