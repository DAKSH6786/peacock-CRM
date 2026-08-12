"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";

type RunDemoButtonProps = {
  propertyId?: string;
};

export function RunDemoButton({ propertyId }: RunDemoButtonProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        disabled={pending}
        onClick={() => {
          setError(null);
          startTransition(async () => {
            try {
              const res = await fetch("/api/intelligence/runs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  propertyId,
                  demo: !propertyId,
                }),
              });
              const data = (await res.json()) as {
                runId?: string;
                error?: string;
                demo?: boolean;
              };
              if (!res.ok) {
                setError(data.error ?? "Failed to start run");
                return;
              }
              if (data.demo) {
                router.push("/intelligence?demo=1");
                router.refresh();
                return;
              }
              router.push(`/intelligence/runs/${data.runId}`);
              router.refresh();
            } catch {
              setError("Network error starting intelligence run");
            }
          });
        }}
      >
        {pending ? "Running cognitive loop…" : "Run OBSERVE → LEARN"}
      </Button>
      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
    </div>
  );
}
