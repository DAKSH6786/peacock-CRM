import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { PrismaAdapter } from "@auth/prisma-adapter";

import { authConfig } from "@/auth.config";
import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import { verifyCredentials } from "@/modules/auth/service";
import { loginSchema } from "@/validations/auth";

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  adapter: PrismaAdapter(prisma),
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const parsed = loginSchema.safeParse(credentials);
        if (!parsed.success) {
          return null;
        }

        const user = await verifyCredentials(
          parsed.data.email,
          parsed.data.password,
        );

        if (!user) {
          return null;
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          organizationId: user.organizationId,
          role: user.role,
          status: user.status,
        };
      },
    }),
  ],
  events: {
    async signIn({ user }) {
      const organizationId = (user as { organizationId?: string | null })
        .organizationId;
      if (organizationId && user.id) {
        await createAuditLog({
          organizationId,
          actorId: user.id,
          action: "LOGIN",
          entityType: "User",
          entityId: user.id,
        });
      }
    },
  },
});
