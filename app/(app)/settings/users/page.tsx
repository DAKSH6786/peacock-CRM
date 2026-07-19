import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/shared/module-placeholder";

export const metadata: Metadata = {
  title: "Users and Roles",
};

export default function Page() {
  return (
    <ModulePlaceholder
      title="Users and Roles"
      description="Membership, roles, and access controls."
    />
  );
}
