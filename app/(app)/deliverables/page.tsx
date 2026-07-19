import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Deliverables",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Deliverables"
      description="Client-facing outputs and approval packages."
    />
  );
}
