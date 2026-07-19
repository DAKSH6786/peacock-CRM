import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "My Work",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="My Work"
      description="Personal queue across tasks, approvals, and follow-ups."
    />
  );
}
