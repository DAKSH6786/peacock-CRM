"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ProgressUpdateForm({
  objectiveId,
  canManage,
}: {
  objectiveId?: string;
  canManage: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!canManage) return null;

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const res = await fetch("/api/progress/updates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        objectiveId: objectiveId ?? null,
        cadence: String(formData.get("cadence") ?? "WEEKLY"),
        periodStart: String(formData.get("periodStart")),
        periodEnd: String(formData.get("periodEnd")),
        body: String(formData.get("body") ?? ""),
        progressPct: formData.get("progressPct")
          ? Number(formData.get("progressPct"))
          : null,
        confidenceScore: formData.get("confidenceScore")
          ? Number(formData.get("confidenceScore"))
          : null,
        riskFlag: formData.get("riskFlag") === "on",
        blocker: String(formData.get("blocker") ?? "") || null,
        evidence: String(formData.get("evidence") ?? "") || null,
      }),
    });
    const data = await res.json();
    setPending(false);
    if (!res.ok) {
      setError(data.error ?? "Failed");
      return;
    }
    router.refresh();
  }

  return (
    <form action={onSubmit} className="space-y-3 rounded-lg border border-[var(--border)] p-4">
      <h3 className="font-semibold">Submit progress update</h3>
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <Label htmlFor="cadence">Cadence</Label>
          <select
            id="cadence"
            name="cadence"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue="WEEKLY"
          >
            <option value="WEEKLY">Weekly</option>
            <option value="MONTHLY">Monthly</option>
          </select>
        </div>
        <div>
          <Label htmlFor="periodStart">Period start</Label>
          <Input id="periodStart" name="periodStart" type="date" required />
        </div>
        <div>
          <Label htmlFor="periodEnd">Period end</Label>
          <Input id="periodEnd" name="periodEnd" type="date" required />
        </div>
        <div>
          <Label htmlFor="progressPct">Progress %</Label>
          <Input id="progressPct" name="progressPct" type="number" min={0} max={100} />
        </div>
        <div>
          <Label htmlFor="confidenceScore">Confidence</Label>
          <Input
            id="confidenceScore"
            name="confidenceScore"
            type="number"
            min={0}
            max={100}
          />
        </div>
        <div className="flex items-end gap-2 pb-2">
          <input id="riskFlag" name="riskFlag" type="checkbox" className="size-4" />
          <Label htmlFor="riskFlag">Risk flag</Label>
        </div>
      </div>
      <div>
        <Label htmlFor="body">Update</Label>
        <textarea
          id="body"
          name="body"
          required
          rows={3}
          className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="blocker">Blocker</Label>
          <Input id="blocker" name="blocker" />
        </div>
        <div>
          <Label htmlFor="evidence">Evidence</Label>
          <Input id="evidence" name="evidence" />
        </div>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <Button type="submit" disabled={pending}>
        {pending ? "Submitting…" : "Submit update"}
      </Button>
    </form>
  );
}

export function HealthOverrideForm({
  objectiveId,
  canManage,
}: {
  objectiveId: string;
  canManage: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!canManage) return null;

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const res = await fetch(`/api/progress/objectives/${objectiveId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        health: String(formData.get("health")),
        healthOverrideReason: String(formData.get("healthOverrideReason") ?? ""),
      }),
    });
    const data = await res.json();
    setPending(false);
    if (!res.ok) {
      setError(data.error ?? "Failed");
      return;
    }
    router.refresh();
  }

  return (
    <form action={onSubmit} className="space-y-2 rounded-lg border border-[var(--border)] p-3">
      <h4 className="text-sm font-semibold">Manual health override</h4>
      <p className="text-xs text-[var(--muted)]">
        Requires a recorded explanation and creates an audit event.
      </p>
      <div className="grid gap-2 sm:grid-cols-3">
        <select
          name="health"
          className="rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          defaultValue="AMBER"
        >
          <option value="GREEN">Green — on track</option>
          <option value="AMBER">Yellow — at risk</option>
          <option value="RED">Red — off track</option>
          <option value="GREY">Grey — insufficient info</option>
        </select>
        <Input
          name="healthOverrideReason"
          placeholder="Explanation (required)"
          required
          className="sm:col-span-1"
        />
        <Button type="submit" size="sm" disabled={pending} variant="secondary">
          {pending ? "Saving…" : "Override"}
        </Button>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
    </form>
  );
}
