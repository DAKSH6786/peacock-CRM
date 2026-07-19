import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "XYME",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="XYME"
      description="Goal management across individuals and teams."
    />
  );
}
