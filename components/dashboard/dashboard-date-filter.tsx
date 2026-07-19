"use client";

import { useRouter, usePathname } from "next/navigation";
import { useState, useTransition } from "react";

import { DateRangePicker } from "@/components/shared/date-range-picker";
import { Button } from "@/components/ui/button";

type DashboardDateFilterProps = {
  from: string;
  to: string;
};

export function DashboardDateFilter({ from, to }: DashboardDateFilterProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [pending, startTransition] = useTransition();
  const [draft, setDraft] = useState({ from, to });
  const draftKey = `${from}|${to}`;
  const [syncedKey, setSyncedKey] = useState(draftKey);

  if (syncedKey !== draftKey) {
    setSyncedKey(draftKey);
    setDraft({ from, to });
  }

  return (
    <form
      className="flex flex-col gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 sm:flex-row sm:items-end"
      onSubmit={(event) => {
        event.preventDefault();
        const params = new URLSearchParams({
          from: draft.from,
          to: draft.to,
        });
        startTransition(() => {
          router.push(`${pathname}?${params.toString()}`);
        });
      }}
    >
      <div className="flex-1">
        <DateRangePicker
          from={draft.from}
          to={draft.to}
          onFromChange={(value) =>
            setDraft((current) => ({ ...current, from: value }))
          }
          onToChange={(value) =>
            setDraft((current) => ({ ...current, to: value }))
          }
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="secondary"
          disabled={pending}
          onClick={() => {
            startTransition(() => {
              router.push(pathname);
            });
          }}
        >
          This month
        </Button>
        <Button type="submit" disabled={pending}>
          {pending ? "Updating…" : "Apply range"}
        </Button>
      </div>
    </form>
  );
}
