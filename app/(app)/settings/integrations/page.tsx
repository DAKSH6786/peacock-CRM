import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Integrations",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Integrations"
      description="Connected systems and credential references."
    />
  );
}
