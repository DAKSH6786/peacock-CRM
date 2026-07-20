import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Timesheets",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Timesheets"
      description="Billable and non-billable time across projects."
    />
  );
}
