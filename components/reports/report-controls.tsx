"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { DateRangePicker } from "@/components/shared/date-range-picker";
import { Button } from "@/components/ui/button";

export function ReportDateFilter({ from, to }: { from: string; to: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const [pending, startTransition] = useTransition();
  const [draft, setDraft] = useState({ from, to });
  const key = `${from}|${to}`;
  const [synced, setSynced] = useState(key);
  if (synced !== key) {
    setSynced(key);
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
        startTransition(() => router.push(`${pathname}?${params.toString()}`));
      }}
    >
      <div className="flex-1">
        <DateRangePicker
          from={draft.from}
          to={draft.to}
          onFromChange={(value) => setDraft((c) => ({ ...c, from: value }))}
          onToChange={(value) => setDraft((c) => ({ ...c, to: value }))}
        />
      </div>
      <div className="flex gap-2">
        <Button
          type="button"
          variant="secondary"
          disabled={pending}
          onClick={() => startTransition(() => router.push(pathname))}
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

export function ReportCategoryNav({
  categories,
}: {
  categories: Array<{ id: string; label: string; count: number }>;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {categories.map((category) => (
        <Link
          key={category.id}
          href={`/reports/${category.id}`}
          className="rounded-full border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--accent-soft)]"
        >
          {category.label} ({category.count})
        </Link>
      ))}
    </div>
  );
}
