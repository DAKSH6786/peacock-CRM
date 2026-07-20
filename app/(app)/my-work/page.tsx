import type { Metadata } from "next";

import { auth } from "@/auth";
import { MyWorkView } from "@/components/my-work/my-work-view";
import { toSessionUser } from "@/lib/session-user";
import { getMyWorkPayload } from "@/modules/dashboard/my-work.service";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "My Work",
};

export default async function MyWorkPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "dashboard:view");

  const payload = await getMyWorkPayload(user!);

  return <MyWorkView payload={payload} />;
}
