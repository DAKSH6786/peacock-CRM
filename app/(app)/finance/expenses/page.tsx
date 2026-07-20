import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Expenses",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Expenses"
      description="Expense claims and operational spend."
    />
  );
}
