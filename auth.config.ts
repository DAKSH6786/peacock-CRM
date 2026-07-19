import type { NextAuthConfig } from "next-auth";

/**
 * Edge-safe Auth.js config used by middleware.
 * Keep this free of Node-only imports (Prisma, bcrypt, etc.).
 */
export const authConfig = {
  pages: {
    signIn: "/login",
  },
  providers: [],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    authorized({ auth, request }) {
      const { pathname } = request.nextUrl;
      const isPublic =
        pathname === "/login" ||
        pathname === "/forgot-password" ||
        pathname.startsWith("/api/health") ||
        pathname.startsWith("/api/auth");

      if (isPublic) {
        return true;
      }

      return Boolean(auth?.user);
    },
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.organizationId =
          (user as { organizationId?: string | null }).organizationId ?? null;
        token.role = (user as { role?: string | null }).role ?? null;
        token.status = (user as { status?: string }).status ?? "ACTIVE";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.organizationId =
          (token.organizationId as string | null) ?? null;
        session.user.role = (token.role as string | null) ?? null;
        session.user.status = (token.status as string) ?? "ACTIVE";
      }
      return session;
    },
  },
  trustHost: true,
} satisfies NextAuthConfig;
