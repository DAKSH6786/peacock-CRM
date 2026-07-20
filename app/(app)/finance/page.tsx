import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Finance",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Finance"
      description="Quotes, invoices, payments, and expenses."
    />
  );
}
