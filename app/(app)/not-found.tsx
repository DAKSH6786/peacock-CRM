import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="peacock-card mx-auto max-w-lg px-6 py-12 text-center">
      <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
        Page not found
      </h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        The page you requested does not exist in Peacock One.
      </p>
      <Button asChild className="mt-6">
        <Link href="/dashboard">Back to dashboard</Link>
      </Button>
    </div>
  );
}
