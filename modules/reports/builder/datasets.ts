import { z } from "zod";

/**
 * Constrained report builder datasets.
 * Browser clients may only reference these whitelisted ids/fields — never SQL.
 */
export const BUILDER_DATASETS = [
  {
    id: "leads",
    label: "Leads",
    permission: "crm:view" as const,
    fields: [
      { id: "source", label: "Source", type: "string" as const },
      { id: "campaign", label: "Campaign", type: "string" as const },
      { id: "country", label: "Country", type: "string" as const },
      { id: "salesperson", label: "Salesperson", type: "string" as const },
      { id: "createdAt", label: "Created date", type: "date" as const },
    ],
    measures: [
      { id: "count", label: "Lead count", format: "number" as const },
      { id: "estimatedValue", label: "Estimated value", format: "money" as const },
    ],
  },
  {
    id: "deals",
    label: "Deals",
    permission: "crm:view" as const,
    fields: [
      { id: "stage", label: "Stage", type: "string" as const },
      { id: "owner", label: "Owner", type: "string" as const },
      { id: "closedAt", label: "Closed date", type: "date" as const },
    ],
    measures: [
      { id: "count", label: "Deal count", format: "number" as const },
      { id: "value", label: "Deal value", format: "money" as const },
    ],
  },
  {
    id: "invoices",
    label: "Invoices",
    permission: "finance:view" as const,
    fields: [
      { id: "status", label: "Status", type: "string" as const },
      { id: "client", label: "Client", type: "string" as const },
      { id: "issueDate", label: "Issue date", type: "date" as const },
    ],
    measures: [
      { id: "count", label: "Invoice count", format: "number" as const },
      { id: "total", label: "Invoice total", format: "money" as const },
      { id: "balance", label: "Outstanding balance", format: "money" as const },
    ],
  },
  {
    id: "payments",
    label: "Payments",
    permission: "finance:view" as const,
    fields: [
      { id: "method", label: "Method", type: "string" as const },
      { id: "receivedAt", label: "Received date", type: "date" as const },
    ],
    measures: [
      { id: "count", label: "Payment count", format: "number" as const },
      { id: "amount", label: "Amount collected", format: "money" as const },
    ],
  },
  {
    id: "projects",
    label: "Projects",
    permission: "projects:view" as const,
    fields: [
      { id: "status", label: "Status", type: "string" as const },
      { id: "name", label: "Project", type: "string" as const },
    ],
    measures: [
      { id: "count", label: "Project count", format: "number" as const },
      { id: "budget", label: "Budget", format: "money" as const },
    ],
  },
  {
    id: "attendance",
    label: "Attendance",
    permission: "hr:view" as const,
    fields: [
      { id: "status", label: "Status", type: "string" as const },
      { id: "date", label: "Date", type: "date" as const },
    ],
    measures: [{ id: "count", label: "Records", format: "number" as const }],
  },
  {
    id: "xyme_goals",
    label: "XYME goals",
    permission: "xyme:view" as const,
    fields: [
      { id: "category", label: "Category", type: "string" as const },
      { id: "department", label: "Department", type: "string" as const },
    ],
    measures: [
      { id: "count", label: "Goal count", format: "number" as const },
      { id: "avgProgress", label: "Average progress", format: "percent" as const },
    ],
  },
] as const;

export type BuilderDatasetId = (typeof BUILDER_DATASETS)[number]["id"];

export const builderDefinitionSchema = z.object({
  datasetId: z.enum([
    "leads",
    "deals",
    "invoices",
    "payments",
    "projects",
    "attendance",
    "xyme_goals",
  ]),
  fields: z.array(z.string().min(1)).max(12),
  filters: z
    .array(
      z.object({
        field: z.string().min(1),
        op: z.enum(["eq", "contains", "gte", "lte"]),
        value: z.string(),
      }),
    )
    .max(10)
    .default([]),
  groupBy: z.array(z.string().min(1)).max(3).default([]),
  measures: z.array(z.string().min(1)).min(1).max(5),
  chartType: z.enum(["bar", "line", "table"]).default("table"),
});

export type BuilderDefinition = z.infer<typeof builderDefinitionSchema>;

export function getBuilderDataset(id: string) {
  return BUILDER_DATASETS.find((dataset) => dataset.id === id);
}
