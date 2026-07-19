import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { LoginForm } from "@/components/auth/login-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Sign in",
};

export default function LoginPage() {
  return (
    <Card>
      <CardHeader>
        <p className="font-[family-name:var(--font-display)] text-3xl text-[var(--brand)]">
          Peacock One
        </p>
        <CardTitle className="mt-2">Sign in</CardTitle>
        <CardDescription>
          Access the Digital Peacock operating system with your work account.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Suspense
          fallback={<p className="text-sm text-[var(--muted)]">Loading…</p>}
        >
          <LoginForm />
        </Suspense>
        <p className="text-sm text-[var(--muted)]">
          Forgot your password?{" "}
          <Link
            href="/forgot-password"
            className="font-medium text-[var(--brand)] underline-offset-4 hover:underline"
          >
            Reset it
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
