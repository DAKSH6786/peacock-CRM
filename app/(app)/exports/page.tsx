import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Exports",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Exports"
      description="Permission-aware export jobs and download history."
    />
  );
}
