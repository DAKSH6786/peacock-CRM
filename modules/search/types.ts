export type SearchCategory =
  | "Leads"
  | "Contacts"
  | "Companies"
  | "Deals"
  | "Projects"
  | "Tasks"
  | "Employees"
  | "Invoices"
  | "Quotes"
  | "Vendors"
  | "Objectives"
  | "Documents";

export type SearchHit = {
  id: string;
  category: SearchCategory;
  title: string;
  subtitle?: string;
  href: string;
};

export type SearchResponse = {
  query: string;
  groups: Array<{ category: SearchCategory; hits: SearchHit[] }>;
};
