import type { Metadata } from "next";
import Link from "next/link";

import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Forgot password",
};

export default function ForgotPasswordPage() {
  return (
    <Card>
      <CardHeader>
        <p className="font-[family-name:var(--font-display)] text-3xl text-[var(--brand)]">
          Peacock One
        </p>
        <CardTitle className="mt-2">Reset password</CardTitle>
        <CardDescription>
          Enter your work email and we will send reset instructions if an
          account exists.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <ForgotPasswordForm />
        <p className="text-sm text-[var(--muted)]">
          Remembered your password?{" "}
          <Link
            href="/login"
            className="font-medium text-[var(--brand)] underline-offset-4 hover:underline"
          >
            Back to sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
