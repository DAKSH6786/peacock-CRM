import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { LoginForm } from "@/components/auth/login-form";
import { Logo } from "@/components/brand/logo";
import { Badge } from "@/components/ui/badge";
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
    <div className="grid w-full items-center gap-10 lg:grid-cols-2">
      <div className="space-y-5">
        <Logo href="/" />
        <Badge tone="teal">Digital Peacock operating system</Badge>
        <h1 className="font-[family-name:var(--font-display)] text-4xl font-bold tracking-tight text-[var(--foreground)] sm:text-5xl lg:text-6xl">
          One OS for growth, delivery, people, and finance.
        </h1>
        <p className="max-w-md text-base text-[var(--muted)]">
          Peacock One unifies CRM, XYME, projects, HR, and billing into a calm,
          permission-aware workspace for creative operators.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            Use your Digital Peacock work account to continue.
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
              className="font-semibold text-[var(--accent-teal)] underline-offset-4 hover:underline"
            >
              Reset it
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
