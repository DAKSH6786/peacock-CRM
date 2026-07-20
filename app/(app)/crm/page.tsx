import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "CRM",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="CRM"
      description="Customer relationships, accounts, and commercial activity."
    />
  );
}
