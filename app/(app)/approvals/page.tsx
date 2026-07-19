import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Approvals",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Approvals"
      description="Pending approval workflows."
    />
  );
}
