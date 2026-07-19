import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Recruitment",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Recruitment"
      description="Open roles and candidate pipeline."
    />
  );
}
