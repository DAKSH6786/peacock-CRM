import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Resources",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Resources"
      description="Workload and capacity planning across teams."
    />
  );
}
