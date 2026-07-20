import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Invoices",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Invoices"
      description="Issued invoices and outstanding balances."
    />
  );
}
