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
    <div
      className="mx-auto max-w-lg rounded-xl border-2 border-black bg-[#ffe17c] px-6 py-12 text-center shadow-[8px_8px_0_0_#000000]"
      role="alert"
    >
      <h1 className="font-[family-name:var(--font-display)] text-3xl font-extrabold tracking-tighter">
        Something went wrong
      </h1>
      <p className="mt-3 font-[family-name:var(--font-body)] text-sm font-medium text-black/70">
        An unexpected error occurred while loading this section. You can try
        again, or contact an administrator if it persists.
      </p>
      <Button className="mt-6" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
