import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Quotes",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Quotes"
      description="Commercial quotes awaiting acceptance."
    />
  );
}
