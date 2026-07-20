import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Tasks",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Tasks"
      description="Assignable work items across projects and operations."
    />
  );
}
