import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "HR",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="HR"
      description="Human resources operations hub."
    />
  );
}
