import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Audit logs",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Audit logs"
      description="Immutable record of sensitive actions."
    />
  );
}
