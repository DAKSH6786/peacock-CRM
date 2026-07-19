import "server-only";

import { auth } from "@/auth";
import type { SessionUser } from "@/permissions";

export async function getSessionUser(): Promise<SessionUser | null> {
  const session = await auth();
  if (!session?.user?.id) {
    return null;
  }

  return {
    id: session.user.id,
    email: session.user.email ?? "",
    name: session.user.name,
    organizationId: session.user.organizationId,
    role: session.user.role as SessionUser["role"],
    status: session.user.status,
  };
}
