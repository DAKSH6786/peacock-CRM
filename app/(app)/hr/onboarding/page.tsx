import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Onboarding",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Onboarding"
      description="Employee onboarding and offboarding checklists."
    />
  );
}
