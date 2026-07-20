export type RevenueDefinition =
  | "sourced"
  | "closed"
  | "invoiced"
  | "collected";

export const REVENUE_DEFINITION_LABELS: Record<RevenueDefinition, string> = {
  sourced: "Sourced revenue — attributed at lead/deal creation",
  closed: "Closed revenue — won deals in the period",
  invoiced: "Invoiced revenue — issued invoices (excludes drafts)",
  collected: "Collected revenue — payments received",
};

export function revenueDefinitionLabel(
  definition: RevenueDefinition | undefined,
): string | null {
  if (!definition) return null;
  return REVENUE_DEFINITION_LABELS[definition];
}
