import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Companies",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Companies"
      description="Client and prospect organizations."
    />
  );
}
