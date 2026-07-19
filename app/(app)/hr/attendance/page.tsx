import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Attendance",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Attendance"
      description="Daily attendance tracking and exceptions."
    />
  );
}
