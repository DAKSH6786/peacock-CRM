import { create } from "zustand";
import { persist } from "zustand/middleware";

type AuthState = {
  accessToken: string | null;
  organisationId: string | null;
  workspaceId: string | null;
  setSession: (session: {
    accessToken: string;
    organisationId: string;
    workspaceId?: string | null;
  }) => void;
  clear: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      organisationId: null,
      workspaceId: null,
      setSession: ({ accessToken, organisationId, workspaceId }) =>
        set({
          accessToken,
          organisationId,
          workspaceId: workspaceId ?? null,
        }),
      clear: () =>
        set({ accessToken: null, organisationId: null, workspaceId: null }),
    }),
    { name: "peacock-auth" },
  ),
);
