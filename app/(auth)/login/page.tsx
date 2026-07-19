import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { LoginForm } from "@/components/auth/login-form";
import { BrowserMockup } from "@/components/brand/browser-mockup";
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
      <div className="space-y-6">
        <Logo href="/" />
        <Badge>INTERNAL OS · DIGITAL PEACOCK</Badge>
        <h1 className="font-[family-name:var(--font-display)] text-5xl font-extrabold tracking-tighter text-black sm:text-6xl lg:text-7xl">
          Run the whole <span className="text-stroke">company</span> from one
          place.
        </h1>
        <p className="max-w-md font-[family-name:var(--font-body)] text-base font-medium text-black/80">
          CRM, delivery, XYME goals, HR, and finance — unified for Digital
          Peacock teams.
        </p>
        <div className="hidden lg:block">
          <BrowserMockup />
        </div>
      </div>

      <Card className="shadow-[8px_8px_0_0_#000000]">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            Use your Digital Peacock work account to access Peacock One.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Suspense
            fallback={
              <p className="text-sm font-medium text-black/60">Loading…</p>
            }
          >
            <LoginForm />
          </Suspense>
          <p className="text-sm font-medium text-black/70">
            Forgot your password?{" "}
            <Link
              href="/forgot-password"
              className="font-bold text-black underline decoration-2 underline-offset-4"
            >
              Reset it
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
