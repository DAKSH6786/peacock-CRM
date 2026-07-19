import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Employees",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Employees"
      description="Directory, roles, and performance context."
    />
  );
}
