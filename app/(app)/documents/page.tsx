import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Documents",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Documents"
      description="Document management and storage."
    />
  );
}
