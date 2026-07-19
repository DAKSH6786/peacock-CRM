import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Vendors",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Vendors"
      description="Vendor directory and payables context."
    />
  );
}
