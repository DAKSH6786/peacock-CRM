"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Lookups = {
  sources: Array<{ id: string; name: string }>;
  statuses: Array<{ id: string; name: string }>;
  pipelines: Array<{
    id: string;
    name: string;
    stages: Array<{ id: string; name: string }>;
  }>;
  users: Array<{ id: string; name: string | null; email: string }>;
  tags: Array<{ id: string; name: string }>;
};

type LeadValues = {
  id?: string;
  personName?: string;
  companyName?: string | null;
  email?: string | null;
  phone?: string | null;
  country?: string | null;
  website?: string | null;
  sourceId?: string | null;
  statusId?: string | null;
  pipelineId?: string | null;
  stageId?: string | null;
  assignedUserId?: string | null;
  estimatedValueMinor?: number | null;
  probability?: number | null;
  notes?: string | null;
  companySize?: string | null;
  budgetMinor?: number | null;
  decisionTimeline?: string | null;
  websiteQuality?: number | null;
  existingRelationship?: boolean;
  interestedServices?: unknown;
  nextFollowUpAt?: string | null;
};

type Props = {
  mode: "create" | "edit";
  lookups: Lookups;
  initial?: LeadValues;
};

export function LeadForm({ mode, lookups, initial }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pipelineId, setPipelineId] = useState(
    initial?.pipelineId ?? lookups.pipelines[0]?.id ?? "",
  );
  const stages =
    lookups.pipelines.find((p) => p.id === pipelineId)?.stages ?? [];

  async function onSubmit(formData: FormData) {
    setBusy(true);
    setError(null);
    const servicesRaw = String(formData.get("interestedServices") ?? "");
    const payload = {
      personName: String(formData.get("personName") ?? ""),
      companyName: String(formData.get("companyName") ?? "") || null,
      email: String(formData.get("email") ?? "") || null,
      phone: String(formData.get("phone") ?? "") || null,
      country: String(formData.get("country") ?? "") || null,
      website: String(formData.get("website") ?? "") || null,
      sourceId: String(formData.get("sourceId") ?? "") || null,
      statusId: String(formData.get("statusId") ?? "") || null,
      pipelineId: String(formData.get("pipelineId") ?? "") || null,
      stageId: String(formData.get("stageId") ?? "") || null,
      assignedUserId: String(formData.get("assignedUserId") ?? "") || null,
      estimatedValueMinor: formData.get("estimatedValue")
        ? Math.round(Number(formData.get("estimatedValue")) * 100)
        : null,
      probability: formData.get("probability")
        ? Number(formData.get("probability"))
        : null,
      notes: String(formData.get("notes") ?? "") || null,
      companySize: String(formData.get("companySize") ?? "") || null,
      budgetMinor: formData.get("budget")
        ? Math.round(Number(formData.get("budget")) * 100)
        : null,
      decisionTimeline: String(formData.get("decisionTimeline") ?? "") || null,
      websiteQuality: formData.get("websiteQuality")
        ? Number(formData.get("websiteQuality"))
        : null,
      existingRelationship: formData.get("existingRelationship") === "on",
      interestedServices: servicesRaw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      nextFollowUpAt: formData.get("nextFollowUpAt")
        ? new Date(String(formData.get("nextFollowUpAt"))).toISOString()
        : null,
    };

    const response = await fetch(
      mode === "create" ? "/api/crm/leads" : `/api/crm/leads/${initial?.id}`,
      {
        method: mode === "create" ? "POST" : "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    const data = await response.json();
    setBusy(false);
    if (!response.ok) {
      setError(data.error ?? "Save failed");
      return;
    }
    router.push(`/crm/leads/${data.lead.id}`);
    router.refresh();
  }

  return (
    <form action={onSubmit} className="grid max-w-3xl gap-4 md:grid-cols-2">
      <div className="md:col-span-2">
        <Label htmlFor="personName">Lead name</Label>
        <Input
          id="personName"
          name="personName"
          required
          defaultValue={initial?.personName ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="companyName">Company</Label>
        <Input
          id="companyName"
          name="companyName"
          defaultValue={initial?.companyName ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          defaultValue={initial?.email ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="phone">Phone</Label>
        <Input id="phone" name="phone" defaultValue={initial?.phone ?? ""} />
      </div>
      <div>
        <Label htmlFor="country">Country</Label>
        <Input
          id="country"
          name="country"
          defaultValue={initial?.country ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="website">Website</Label>
        <Input
          id="website"
          name="website"
          defaultValue={initial?.website ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="sourceId">Source</Label>
        <select
          id="sourceId"
          name="sourceId"
          className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
          defaultValue={initial?.sourceId ?? ""}
        >
          <option value="">Select</option>
          {lookups.sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="statusId">Status</Label>
        <select
          id="statusId"
          name="statusId"
          className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
          defaultValue={initial?.statusId ?? ""}
        >
          <option value="">Select</option>
          {lookups.statuses.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="pipelineId">Pipeline</Label>
        <select
          id="pipelineId"
          name="pipelineId"
          className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
          value={pipelineId}
          onChange={(e) => setPipelineId(e.target.value)}
        >
          {lookups.pipelines.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="stageId">Stage</Label>
        <select
          id="stageId"
          name="stageId"
          className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
          defaultValue={initial?.stageId ?? stages[0]?.id ?? ""}
        >
          {stages.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="assignedUserId">Assigned salesperson</Label>
        <select
          id="assignedUserId"
          name="assignedUserId"
          className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
          defaultValue={initial?.assignedUserId ?? ""}
        >
          <option value="">Unassigned</option>
          {lookups.users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name ?? u.email}
            </option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="estimatedValue">Estimated value</Label>
        <Input
          id="estimatedValue"
          name="estimatedValue"
          type="number"
          step="0.01"
          defaultValue={
            initial?.estimatedValueMinor != null
              ? initial.estimatedValueMinor / 100
              : ""
          }
        />
      </div>
      <div>
        <Label htmlFor="interestedServices">Interested services</Label>
        <Input
          id="interestedServices"
          name="interestedServices"
          placeholder="Brand, Web, SEO"
          defaultValue={
            Array.isArray(initial?.interestedServices)
              ? initial?.interestedServices.join(", ")
              : ""
          }
        />
      </div>
      <div>
        <Label htmlFor="companySize">Company size</Label>
        <Input
          id="companySize"
          name="companySize"
          placeholder="smb / mid / enterprise"
          defaultValue={initial?.companySize ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="budget">Budget</Label>
        <Input
          id="budget"
          name="budget"
          type="number"
          step="0.01"
          defaultValue={
            initial?.budgetMinor != null ? initial.budgetMinor / 100 : ""
          }
        />
      </div>
      <div>
        <Label htmlFor="decisionTimeline">Decision timeline</Label>
        <Input
          id="decisionTimeline"
          name="decisionTimeline"
          placeholder="30 days"
          defaultValue={initial?.decisionTimeline ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="websiteQuality">Website quality (0-10)</Label>
        <Input
          id="websiteQuality"
          name="websiteQuality"
          type="number"
          min={0}
          max={10}
          defaultValue={initial?.websiteQuality ?? ""}
        />
      </div>
      <div>
        <Label htmlFor="nextFollowUpAt">Next follow-up</Label>
        <Input
          id="nextFollowUpAt"
          name="nextFollowUpAt"
          type="datetime-local"
          defaultValue={
            initial?.nextFollowUpAt
              ? initial.nextFollowUpAt.slice(0, 16)
              : ""
          }
        />
      </div>
      <div className="flex items-center gap-2 pt-6">
        <input
          id="existingRelationship"
          name="existingRelationship"
          type="checkbox"
          defaultChecked={initial?.existingRelationship ?? false}
        />
        <Label htmlFor="existingRelationship">Existing relationship</Label>
      </div>
      <div className="md:col-span-2">
        <Label htmlFor="notes">Notes</Label>
        <textarea
          id="notes"
          name="notes"
          className="min-h-24 w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
          defaultValue={initial?.notes ?? ""}
        />
      </div>
      {error ? (
        <p className="md:col-span-2 text-sm text-[var(--danger)]">{error}</p>
      ) : null}
      <div className="md:col-span-2">
        <Button type="submit" disabled={busy}>
          {busy ? "Saving…" : mode === "create" ? "Create lead" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
