import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Leads",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Leads"
      description="Capture and qualify inbound and outbound leads."
    />
  );
}
