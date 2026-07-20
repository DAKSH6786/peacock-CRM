"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  parents: Array<{ id: string; title: string; scope: string }>;
  departments: Array<{ id: string; name: string }>;
};

export function ObjectiveCreateForm({ parents, departments }: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const payload = {
      title: String(formData.get("title") ?? ""),
      description: String(formData.get("description") ?? "") || null,
      scope: String(formData.get("scope") ?? "COMPANY"),
      parentId: String(formData.get("parentId") ?? "") || null,
      departmentId: String(formData.get("departmentId") ?? "") || null,
      quarter: String(formData.get("quarter") ?? "") || null,
      priority: String(formData.get("priority") ?? "MEDIUM"),
      startDate: String(formData.get("startDate") ?? "") || null,
      dueDate: String(formData.get("dueDate") ?? "") || null,
      tags: String(formData.get("tags") ?? "")
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    };

    const res = await fetch("/api/progress/objectives", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    setPending(false);
    if (!res.ok) {
      setError(data.error ?? "Failed to create objective");
      return;
    }
    setOpen(false);
    router.push(`/company-progress/objectives/${data.objective.id}`);
    router.refresh();
  }

  if (!open) {
    return (
      <Button type="button" onClick={() => setOpen(true)}>
        New objective
      </Button>
    );
  }

  return (
    <form
      action={onSubmit}
      className="w-full max-w-xl space-y-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Create objective</h3>
        <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
          Cancel
        </Button>
      </div>
      <div>
        <Label htmlFor="title">Title</Label>
        <Input id="title" name="title" required maxLength={300} />
      </div>
      <div>
        <Label htmlFor="description">Description</Label>
        <textarea
          id="description"
          name="description"
          className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          rows={3}
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="scope">Level</Label>
          <select
            id="scope"
            name="scope"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue="COMPANY"
          >
            <option value="COMPANY">Company</option>
            <option value="DEPARTMENT">Department</option>
            <option value="TEAM">Team</option>
            <option value="INDIVIDUAL">Individual</option>
          </select>
        </div>
        <div>
          <Label htmlFor="priority">Priority</Label>
          <select
            id="priority"
            name="priority"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue="MEDIUM"
          >
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
        <div>
          <Label htmlFor="parentId">Parent objective</Label>
          <select
            id="parentId"
            name="parentId"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue=""
          >
            <option value="">None</option>
            {parents.map((p) => (
              <option key={p.id} value={p.id}>
                [{p.scope}] {p.title}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor="departmentId">Department</Label>
          <select
            id="departmentId"
            name="departmentId"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue=""
          >
            <option value="">None</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor="quarter">Quarter</Label>
          <Input id="quarter" name="quarter" placeholder="Q1" />
        </div>
        <div>
          <Label htmlFor="tags">Tags</Label>
          <Input id="tags" name="tags" placeholder="growth, retention" />
        </div>
        <div>
          <Label htmlFor="startDate">Start date</Label>
          <Input id="startDate" name="startDate" type="date" />
        </div>
        <div>
          <Label htmlFor="dueDate">End date</Label>
          <Input id="dueDate" name="dueDate" type="date" />
        </div>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <Button type="submit" disabled={pending}>
        {pending ? "Saving…" : "Create"}
      </Button>
    </form>
  );
}
