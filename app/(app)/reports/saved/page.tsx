import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Saved Reports",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Saved Reports"
      description="Pinned analytics views for your role."
    />
  );
}
