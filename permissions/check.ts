import "server-only";

import type { MembershipRole } from "@prisma/client";

import { hasPermission, type Permission, type SessionUser } from "./types";

export class UnauthorizedError extends Error {
  constructor(message = "Unauthorized") {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends Error {
  constructor(message = "Forbidden") {
    super(message);
    this.name = "ForbiddenError";
  }
}

export function requireUser(user: SessionUser | null | undefined): SessionUser {
  if (!user?.id) {
    throw new UnauthorizedError("Authentication required");
  }
  return user;
}

export function requirePermission(
  user: SessionUser | null | undefined,
  permission: Permission,
): SessionUser {
  const authed = requireUser(user);

  if (!hasPermission(authed.role as MembershipRole | null, permission)) {
    throw new ForbiddenError(`Missing permission: ${permission}`);
  }

  return authed;
}

export function requireOrganization(
  user: SessionUser | null | undefined,
): SessionUser & { organizationId: string } {
  const authed = requireUser(user);

  if (!authed.organizationId) {
    throw new ForbiddenError("User is not assigned to an organization");
  }

  return authed as SessionUser & { organizationId: string };
}
