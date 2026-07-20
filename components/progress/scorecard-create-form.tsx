"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  departments: Array<{ id: string; name: string; code: string }>;
  templates: Record<
    string,
    Array<{ code: string; name: string; category: string; unit?: string }>
  >;
};

export function ScorecardCreateForm({ departments, templates }: Props) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const templateKeys = Object.keys(templates);

  async function onSubmit(formData: FormData) {
    setPending(true);
    setError(null);
    const res = await fetch("/api/progress/scorecards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        departmentId: String(formData.get("departmentId")),
        name: String(formData.get("name") ?? "Scorecard"),
        description: String(formData.get("description") ?? "") || null,
        templateCode: String(formData.get("templateCode") ?? "") || undefined,
        kpiIds: [],
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
    <form
      action={onSubmit}
      className="space-y-3 rounded-lg border border-[var(--border)] p-4"
    >
      <h3 className="font-semibold">Configure department scorecard</h3>
      <p className="text-xs text-[var(--muted)]">
        Choose a department-specific KPI template. Templates are optional
        starting points — departments do not share one forced metric set.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="departmentId">Department</Label>
          <select
            id="departmentId"
            name="departmentId"
            required
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue=""
          >
            <option value="" disabled>
              Select…
            </option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor="templateCode">KPI template</Label>
          <select
            id="templateCode"
            name="templateCode"
            className="mt-1 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            defaultValue={templateKeys[0] ?? ""}
          >
            {templateKeys.map((key) => (
              <option key={key} value={key}>
                {key} ({templates[key]?.length ?? 0} KPIs)
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor="name">Scorecard name</Label>
          <Input id="name" name="name" defaultValue="FY scorecard" required />
        </div>
        <div>
          <Label htmlFor="description">Description</Label>
          <Input id="description" name="description" />
        </div>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <Button type="submit" disabled={pending}>
        {pending ? "Saving…" : "Save scorecard"}
      </Button>
    </form>
  );
}
