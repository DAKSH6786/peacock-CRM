import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Payments",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Payments"
      description="Incoming and outgoing payment records."
    />
  );
}
