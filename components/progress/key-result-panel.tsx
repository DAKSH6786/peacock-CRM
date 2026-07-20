"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function KeyResultPanel({
  objectiveId,
  canManage,
}: {
  objectiveId: string;
  canManage: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (!canManage) return null;

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const payload = {
      objectiveId,
      title: String(formData.get("title") ?? ""),
      metricType: String(formData.get("metricType") ?? "NUMBER"),
      baseline: formData.get("baseline")
        ? Number(formData.get("baseline"))
        : null,
      target: formData.get("target") ? Number(formData.get("target")) : null,
      currentValue: formData.get("currentValue")
        ? Number(formData.get("currentValue"))
        : null,
      unit: String(formData.get("unit") ?? "") || null,
      updateFrequency: String(formData.get("updateFrequency") ?? "WEEKLY"),
      confidenceScore: formData.get("confidenceScore")
        ? Number(formData.get("confidenceScore"))
        : null,
      dueDate: String(formData.get("dueDate") ?? "") || null,
      evidence: String(formData.get("evidence") ?? "") || null,
    };

    const res = await fetch("/api/progress/key-results", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
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
    <form action={onSubmit} className="mt-4 space-y-3 border-t border-[var(--border)] pt-4">
      <h4 className="text-sm font-semibold">Add key result</h4>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label htmlFor="kr-title">Title</Label>
          <Input id="kr-title" name="title" required />
        </div>
        <div>
          <Label htmlFor="metricType">Measurement type</Label>
          <select
            id="metricType"
            name="metricType"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue="NUMBER"
          >
            <option value="NUMBER">Number</option>
            <option value="CURRENCY">Currency</option>
            <option value="PERCENT">Percentage</option>
            <option value="BOOLEAN">Boolean</option>
            <option value="MILESTONE">Milestone</option>
            <option value="CUSTOM">Custom unit</option>
          </select>
        </div>
        <div>
          <Label htmlFor="unit">Unit</Label>
          <Input id="unit" name="unit" placeholder="%, INR, deals" />
        </div>
        <div>
          <Label htmlFor="baseline">Baseline</Label>
          <Input id="baseline" name="baseline" type="number" step="any" />
        </div>
        <div>
          <Label htmlFor="target">Target</Label>
          <Input id="target" name="target" type="number" step="any" />
        </div>
        <div>
          <Label htmlFor="currentValue">Current value</Label>
          <Input id="currentValue" name="currentValue" type="number" step="any" />
        </div>
        <div>
          <Label htmlFor="updateFrequency">Update frequency</Label>
          <select
            id="updateFrequency"
            name="updateFrequency"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue="WEEKLY"
          >
            <option value="WEEKLY">Weekly</option>
            <option value="MONTHLY">Monthly</option>
            <option value="QUARTERLY">Quarterly</option>
            <option value="AD_HOC">Ad hoc</option>
          </select>
        </div>
        <div>
          <Label htmlFor="confidenceScore">Confidence (0–100)</Label>
          <Input
            id="confidenceScore"
            name="confidenceScore"
            type="number"
            min={0}
            max={100}
          />
        </div>
        <div>
          <Label htmlFor="dueDate">Due date</Label>
          <Input id="dueDate" name="dueDate" type="date" />
        </div>
        <div className="sm:col-span-2">
          <Label htmlFor="evidence">Evidence</Label>
          <Input id="evidence" name="evidence" />
        </div>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <Button type="submit" disabled={pending} size="sm">
        {pending ? "Adding…" : "Add key result"}
      </Button>
    </form>
  );
}

export function KeyResultUpdateForm({
  keyResultId,
  canManage,
}: {
  keyResultId: string;
  canManage: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!canManage) return null;

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const res = await fetch("/api/progress/key-results", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "record-value",
        keyResultId,
        newValue: Number(formData.get("newValue")),
        confidenceScore: formData.get("confidenceScore")
          ? Number(formData.get("confidenceScore"))
          : null,
        note: String(formData.get("note") ?? "") || null,
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
    <form action={onSubmit} className="mt-2 grid gap-2 sm:grid-cols-4">
      <Input name="newValue" type="number" step="any" placeholder="New value" required />
      <Input
        name="confidenceScore"
        type="number"
        min={0}
        max={100}
        placeholder="Confidence"
      />
      <Input name="note" placeholder="Note / comment" />
      <Button type="submit" size="sm" disabled={pending}>
        {pending ? "Saving…" : "Record update"}
      </Button>
      <Input name="evidence" placeholder="Evidence link / note" className="sm:col-span-3" />
      {error ? <p className="text-sm text-rose-600 sm:col-span-4">{error}</p> : null}
    </form>
  );
}
