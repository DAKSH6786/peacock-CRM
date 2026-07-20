import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Company progress",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Company progress"
      description="Organization-level objectives and progress."
    />
  );
}
