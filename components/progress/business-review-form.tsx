"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function BusinessReviewCreateForm({ canManage }: { canManage: boolean }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!canManage) return null;

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const itemsRaw = String(formData.get("actionItems") ?? "");
    const items = itemsRaw
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((title) => ({
        itemType: "ACTION" as const,
        title,
        body: null,
        ownerUserId: null,
        dueDate: null,
      }));

    const res = await fetch("/api/progress/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: String(formData.get("title") ?? ""),
        reviewType: String(formData.get("reviewType") ?? "MONTHLY"),
        periodStart: String(formData.get("periodStart")),
        periodEnd: String(formData.get("periodEnd")),
        summary: String(formData.get("summary") ?? "") || null,
        majorWins: String(formData.get("majorWins") ?? "") || null,
        missedTargets: String(formData.get("missedTargets") ?? "") || null,
        items: [
          ...items,
          ...String(formData.get("risks") ?? "")
            .split("\n")
            .map((line) => line.trim())
            .filter(Boolean)
            .map((title) => ({
              itemType: "RISK" as const,
              title,
              body: null,
              ownerUserId: null,
              dueDate: null,
            })),
          ...String(formData.get("decisions") ?? "")
            .split("\n")
            .map((line) => line.trim())
            .filter(Boolean)
            .map((title) => ({
              itemType: "DECISION" as const,
              title,
              body: null,
              ownerUserId: null,
              dueDate: null,
            })),
        ],
      }),
    });
    const data = await res.json();
    setPending(false);
    if (!res.ok) {
      setError(data.error ?? "Failed");
      return;
    }
    router.push(`/company-progress/reviews/${data.review.id}`);
    router.refresh();
  }

  return (
    <form
      action={onSubmit}
      className="space-y-3 rounded-lg border border-[var(--border)] p-4 print:hidden"
    >
      <h3 className="font-semibold">Create business review</h3>
      <p className="text-xs text-[var(--muted)]">
        Snapshots KPI values, objective progress, and open risks at creation
        time.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label htmlFor="title">Title</Label>
          <Input id="title" name="title" required />
        </div>
        <div>
          <Label htmlFor="reviewType">Type</Label>
          <select
            id="reviewType"
            name="reviewType"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue="MONTHLY"
          >
            <option value="MONTHLY">Monthly</option>
            <option value="QUARTERLY">Quarterly</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label htmlFor="periodStart">Start</Label>
            <Input id="periodStart" name="periodStart" type="date" required />
          </div>
          <div>
            <Label htmlFor="periodEnd">End</Label>
            <Input id="periodEnd" name="periodEnd" type="date" required />
          </div>
        </div>
      </div>
      <div>
        <Label htmlFor="summary">Summary</Label>
        <textarea
          id="summary"
          name="summary"
          rows={2}
          className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="majorWins">Major wins</Label>
          <textarea
            id="majorWins"
            name="majorWins"
            rows={2}
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <Label htmlFor="missedTargets">Missed targets</Label>
          <textarea
            id="missedTargets"
            name="missedTargets"
            rows={2}
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <Label htmlFor="risks">Risks (one per line)</Label>
          <textarea
            id="risks"
            name="risks"
            rows={2}
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <Label htmlFor="decisions">Decisions (one per line)</Label>
          <textarea
            id="decisions"
            name="decisions"
            rows={2}
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div className="sm:col-span-2">
          <Label htmlFor="actionItems">Action items (one per line)</Label>
          <textarea
            id="actionItems"
            name="actionItems"
            rows={2}
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </div>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <Button type="submit" disabled={pending}>
        {pending ? "Creating…" : "Create review snapshot"}
      </Button>
    </form>
  );
}
