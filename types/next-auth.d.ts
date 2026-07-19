import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      organizationId: string | null;
      role: string | null;
      status: string;
    } & DefaultSession["user"];
  }

  interface User {
    organizationId?: string | null;
    role?: string | null;
    status?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string;
    organizationId?: string | null;
    role?: string | null;
    status?: string;
  }
}
