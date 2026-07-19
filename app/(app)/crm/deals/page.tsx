import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Deals",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Deals"
      description="Commercial opportunities linked to pipeline stages."
    />
  );
}
