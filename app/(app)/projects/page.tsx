import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Projects",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Projects"
      description="Delivery ERP for scoped client work."
    />
  );
}
