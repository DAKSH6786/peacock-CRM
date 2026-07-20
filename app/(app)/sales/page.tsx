import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Sales",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Sales"
      description="Sales performance, cost versus revenue, and targets."
    />
  );
}
