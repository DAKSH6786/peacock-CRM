import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Leaves",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Leaves"
      description="Leave requests, balances, and approvals."
    />
  );
}
