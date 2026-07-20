import type { DashboardDateRange } from "@/modules/dashboard/date-range";
import type { DashboardPersona } from "@/modules/dashboard/persona";

export type MetricValue = {
  label: string;
  value: number;
  format: "number" | "money" | "percent";
  currencyCode?: string;
  hint?: string;
};

export type NamedCount = { name: string; value: number };

export type DashboardPayload = {
  persona: DashboardPersona;
  range: DashboardDateRange;
  currencyCode: string;
  metrics: MetricValue[];
  charts: Array<{
    id: string;
    title: string;
    description?: string;
    data: NamedCount[];
  }>;
  lists: Array<{
    id: string;
    title: string;
    items: Array<{ id: string; title: string; meta?: string; href?: string }>;
  }>;
  activity: Array<{
    id: string;
    title: string;
    description?: string;
    at: string;
  }>;
};
