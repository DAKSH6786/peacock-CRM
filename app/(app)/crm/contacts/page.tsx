import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Contacts",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Contacts"
      description="People associated with companies and opportunities."
    />
  );
}
