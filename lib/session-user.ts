import type { Session } from "next-auth";

import type { SessionUser } from "@/permissions";

export function toSessionUser(
  session: Session | null,
): SessionUser | null {
  if (!session?.user?.id) return null;
  return {
    id: session.user.id,
    email: session.user.email ?? "",
    name: session.user.name,
    organizationId: session.user.organizationId,
    role: session.user.role as SessionUser["role"],
    status: session.user.status,
  };
}
