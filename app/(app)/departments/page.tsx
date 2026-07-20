import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Departments",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Departments"
      description="Department structure and progress tracking."
    />
  );
}
