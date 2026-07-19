import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Policies",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Policies"
      description="Company policies and acknowledgement tracking."
    />
  );
}
