"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

type TokenResponse = {
  access_token: string;
  organisation_id: string;
  workspace_id?: string | null;
};

type MeResponse = {
  email: string;
  organisation_name: string;
  roles: string[];
};

export function LoginForm() {
  const { accessToken, setSession, clear } = useAuthStore();
  const [email, setEmail] = useState("admin@peacock.one");
  const [password, setPassword] = useState("ChangeMeNow!123");
  const [error, setError] = useState<string | null>(null);

  const me = useQuery({
    queryKey: ["me", accessToken],
    enabled: Boolean(accessToken),
    queryFn: () =>
      apiFetch<MeResponse>("/auth/me", { token: accessToken ?? undefined }),
  });

  const login = useMutation({
    mutationFn: () =>
      apiFetch<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    onSuccess: (data) => {
      setError(null);
      setSession({
        accessToken: data.access_token,
        organisationId: data.organisation_id,
        workspaceId: data.workspace_id,
      });
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        Auth scaffold
      </h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Email/password now. Google & Microsoft OAuth endpoints are prepared.
      </p>

      {accessToken && me.data ? (
        <div className="mt-6 space-y-3 text-sm">
          <p>
            Signed in as <strong>{me.data.email}</strong>
          </p>
          <p className="text-[var(--muted)]">
            {me.data.organisation_name} · roles: {me.data.roles.join(", ")}
          </p>
          <Button type="button" variant="secondary" onClick={() => clear()}>
            Sign out
          </Button>
        </div>
      ) : (
        <form
          className="mt-6 space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            login.mutate();
          }}
        >
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Email</span>
            <input
              className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Password</span>
            <input
              type="password"
              className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
          <Button type="submit" disabled={login.isPending}>
            {login.isPending ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      )}
    </section>
  );
}
