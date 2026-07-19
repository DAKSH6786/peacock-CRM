import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Pipeline",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Pipeline"
      description="Visual sales stages and deal progression."
    />
  );
}
