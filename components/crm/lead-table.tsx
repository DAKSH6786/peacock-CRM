"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type LeadRow = {
  id: string;
  personName: string;
  companyName: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  estimatedValueMinor: number | null;
  currencyCode: string;
  leadScore: number;
  probability: number | null;
  lastContactedAt: string | null;
  nextFollowUpAt: string | null;
  ageDays: number;
  stale: boolean;
  source?: { name: string } | null;
  status?: { name: string } | null;
  stage?: { name: string; color: string | null } | null;
  assignedUser?: { id: string; name: string | null; email: string } | null;
  tags: Array<{ id: string; name: string; color: string | null }>;
  interestedServices?: unknown;
};

type Lookup = {
  sources: Array<{ id: string; name: string }>;
  statuses: Array<{ id: string; name: string }>;
  pipelines: Array<{
    id: string;
    name: string;
    stages: Array<{ id: string; name: string }>;
  }>;
  tags: Array<{ id: string; name: string }>;
  users: Array<{ id: string; name: string | null; email: string }>;
  lostReasons: Array<{ id: string; name: string }>;
};

type Props = {
  initialLeads: LeadRow[];
  lookups: Lookup;
  canManage: boolean;
  canExport: boolean;
};

function money(minor: number | null | undefined, currency: string) {
  if (minor == null) return "—";
  return `${currency} ${(minor / 100).toLocaleString()}`;
}

function servicesLabel(value: unknown): string {
  if (!value) return "—";
  if (Array.isArray(value)) return value.map(String).join(", ") || "—";
  return String(value);
}

export function LeadTable({
  initialLeads,
  lookups,
  canManage,
  canExport,
}: Props) {
  const router = useRouter();
  const [leads, setLeads] = useState(initialLeads);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [q, setQ] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [statusId, setStatusId] = useState("");
  const [stageId, setStageId] = useState("");
  const [assignedUserId, setAssignedUserId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const stages = lookups.pipelines.flatMap((p) => p.stages);

  const filtered = useMemo(() => {
    return leads.filter((lead) => {
      if (sourceId && lead.source && !lookups.sources.find((s) => s.id === sourceId && s.name === lead.source?.name)) {
        // filter client-side by reloading preferred; keep simple text match
      }
      if (q) {
        const hay = `${lead.personName} ${lead.companyName ?? ""} ${lead.email ?? ""}`.toLowerCase();
        if (!hay.includes(q.toLowerCase())) return false;
      }
      if (assignedUserId && lead.assignedUser?.id !== assignedUserId) return false;
      if (statusId && lead.status && !lookups.statuses.some((s) => s.id === statusId && s.name === lead.status?.name)) {
        return lead.status?.name !== lookups.statuses.find((s) => s.id === statusId)?.name;
      }
      return true;
    });
  }, [leads, q, assignedUserId, statusId, sourceId, lookups]);

  async function reload() {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (sourceId) params.set("sourceId", sourceId);
    if (statusId) params.set("statusId", statusId);
    if (stageId) params.set("stageId", stageId);
    if (assignedUserId) params.set("assignedUserId", assignedUserId);
    const response = await fetch(`/api/crm/leads?${params.toString()}`);
    if (!response.ok) return;
    const data = await response.json();
    setLeads(
      data.leads.map((lead: LeadRow & { createdAt?: string }) => ({
        ...lead,
        lastContactedAt: lead.lastContactedAt,
        nextFollowUpAt: lead.nextFollowUpAt,
      })),
    );
  }

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function bulk(action: string, payload: Record<string, unknown>) {
    const response = await fetch("/api/crm/leads", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        action,
        leadIds: [...selected],
        ...payload,
      }),
    });
    const data = await response.json();
    setMessage(response.ok ? "Bulk update applied" : data.error);
    setSelected(new Set());
    await reload();
    router.refresh();
  }

  function exportCsv() {
    if (!canExport) return;
    const headers = [
      "Name",
      "Company",
      "Email",
      "Phone",
      "Country",
      "Source",
      "Services",
      "Value",
      "Owner",
      "Stage",
      "Score",
      "Probability",
      "Last contacted",
      "Next follow-up",
      "Age",
      "Status",
    ];
    const rows = filtered.map((l) =>
      [
        l.personName,
        l.companyName ?? "",
        l.email ?? "",
        l.phone ?? "",
        l.country ?? "",
        l.source?.name ?? "",
        servicesLabel(l.interestedServices),
        money(l.estimatedValueMinor, l.currencyCode),
        l.assignedUser?.name ?? l.assignedUser?.email ?? "",
        l.stage?.name ?? "",
        l.leadScore,
        l.probability ?? "",
        l.lastContactedAt?.slice(0, 10) ?? "",
        l.nextFollowUpAt?.slice(0, 10) ?? "",
        l.ageDays,
        l.status?.name ?? "",
      ]
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(","),
    );
    const blob = new Blob([[headers.join(","), ...rows].join("\n")], {
      type: "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Input
          placeholder="Search leads"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-xs"
        />
        <select
          className="rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
        >
          <option value="">All sources</option>
          {lookups.sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
          value={statusId}
          onChange={(e) => setStatusId(e.target.value)}
        >
          <option value="">All statuses</option>
          {lookups.statuses.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
          value={stageId}
          onChange={(e) => setStageId(e.target.value)}
        >
          <option value="">All stages</option>
          {stages.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
          value={assignedUserId}
          onChange={(e) => setAssignedUserId(e.target.value)}
        >
          <option value="">All owners</option>
          {lookups.users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name ?? u.email}
            </option>
          ))}
        </select>
        <Button
          type="button"
          variant="secondary"
          disabled={pending}
          onClick={() => startTransition(() => void reload())}
        >
          Apply filters
        </Button>
        {canExport ? (
          <Button type="button" variant="secondary" onClick={exportCsv}>
            Export
          </Button>
        ) : null}
      </div>

      {canManage && selected.size > 0 ? (
        <div className="flex flex-wrap items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-2)] p-3">
          <span className="text-sm">{selected.size} selected</span>
          <select
            id="bulk-owner"
            className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-sm"
            defaultValue=""
            onChange={(e) => {
              if (!e.target.value) return;
              void bulk("bulk-assign", {
                assignedUserId: e.target.value === "__none__" ? null : e.target.value,
              });
            }}
          >
            <option value="">Assign to…</option>
            <option value="__none__">Unassigned</option>
            {lookups.users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name ?? u.email}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-sm"
            defaultValue=""
            onChange={(e) => {
              if (!e.target.value) return;
              void bulk("bulk-stage", {
                stageId: e.target.value,
                confirmClose: true,
              });
            }}
          >
            <option value="">Move stage…</option>
            {stages.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-[var(--border)] bg-[var(--background)] px-2 py-1 text-sm"
            defaultValue=""
            onChange={(e) => {
              if (!e.target.value) return;
              void bulk("bulk-tags", { tagIds: [e.target.value], mode: "ADD" });
            }}
          >
            <option value="">Add tag…</option>
            {lookups.tags.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {message ? <p className="text-sm">{message}</p> : null}

      <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-[var(--surface-2)] text-xs uppercase tracking-wide text-[var(--muted)]">
            <tr>
              {canManage ? <th className="px-3 py-2" /> : null}
              <th className="px-3 py-2">Lead</th>
              <th className="px-3 py-2">Company</th>
              <th className="px-3 py-2">Contact</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Services</th>
              <th className="px-3 py-2">Value</th>
              <th className="px-3 py-2">Owner</th>
              <th className="px-3 py-2">Stage</th>
              <th className="px-3 py-2">Score</th>
              <th className="px-3 py-2">Prob.</th>
              <th className="px-3 py-2">Last / Next</th>
              <th className="px-3 py-2">Age</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((lead) => (
              <tr
                key={lead.id}
                className="border-t border-[var(--border)] hover:bg-[var(--surface-2)]/60"
              >
                {canManage ? (
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={selected.has(lead.id)}
                      onChange={() => toggle(lead.id)}
                    />
                  </td>
                ) : null}
                <td className="px-3 py-2 font-medium">
                  <Link href={`/crm/leads/${lead.id}`} className="hover:underline">
                    {lead.personName}
                  </Link>
                  {lead.stale ? (
                    <Badge className="ml-2" tone="default">
                      Stale
                    </Badge>
                  ) : null}
                </td>
                <td className="px-3 py-2">{lead.companyName ?? "—"}</td>
                <td className="px-3 py-2">
                  <div>{lead.email ?? "—"}</div>
                  <div className="text-xs text-[var(--muted)]">{lead.phone}</div>
                  <div className="text-xs text-[var(--muted)]">{lead.country}</div>
                </td>
                <td className="px-3 py-2">{lead.source?.name ?? "—"}</td>
                <td className="px-3 py-2">{servicesLabel(lead.interestedServices)}</td>
                <td className="px-3 py-2">
                  {money(lead.estimatedValueMinor, lead.currencyCode)}
                </td>
                <td className="px-3 py-2">
                  {lead.assignedUser?.name ?? lead.assignedUser?.email ?? "—"}
                </td>
                <td className="px-3 py-2">
                  <span
                    className="inline-flex rounded px-2 py-0.5 text-xs"
                    style={{
                      backgroundColor: lead.stage?.color
                        ? `${lead.stage.color}22`
                        : undefined,
                    }}
                  >
                    {lead.stage?.name ?? "—"}
                  </span>
                </td>
                <td className="px-3 py-2">{lead.leadScore}</td>
                <td className="px-3 py-2">{lead.probability ?? "—"}%</td>
                <td className="px-3 py-2 text-xs">
                  <div>{lead.lastContactedAt?.slice(0, 10) ?? "—"}</div>
                  <div className="text-[var(--muted)]">
                    {lead.nextFollowUpAt?.slice(0, 10) ?? "—"}
                  </div>
                </td>
                <td className="px-3 py-2">{lead.ageDays}d</td>
                <td className="px-3 py-2">{lead.status?.name ?? "—"}</td>
                <td className="px-3 py-2">
                  <div className="flex gap-1">
                    <Button asChild size="sm" variant="ghost">
                      <Link href={`/crm/leads/${lead.id}`}>Open</Link>
                    </Button>
                    {canManage ? (
                      <Button asChild size="sm" variant="ghost">
                        <Link href={`/crm/leads/${lead.id}?edit=1`}>Edit</Link>
                      </Button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 ? (
          <p className="p-6 text-sm text-[var(--muted)]">No leads match.</p>
        ) : null}
      </div>
    </div>
  );
}
