import type { Metadata } from "next";

import { auth } from "@/auth";
import BuilderPreviewClient from "@/app/(app)/reports/builder/preview/preview-client";
import { PageHeader } from "@/components/shared/page-header";
import { toSessionUser } from "@/lib/session-user";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Builder preview",
};

export default async function BuilderPreviewPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "reports:view");

  return (
    <div>
      <PageHeader
        title="Builder preview"
        description="Live preview of your constrained builder definition."
      />
      <BuilderPreviewClient canExport={false} />
    </div>
  );
}
