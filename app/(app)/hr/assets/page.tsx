import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Assets",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Assets"
      description="Company assets assigned to employees."
    />
  );
}
