"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-lg py-16 text-center" role="alert">
      <h1 className="font-[family-name:var(--font-display)] text-2xl">
        Something went wrong
      </h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        An unexpected error occurred while loading this section. You can try
        again, or contact an administrator if it persists.
      </p>
      <Button className="mt-6" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
