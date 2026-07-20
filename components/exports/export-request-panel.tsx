"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ExportDefinition } from "@/modules/exports";

type Props = {
  catalog: ExportDefinition[];
};

export function ExportRequestPanel({ catalog }: Props) {
  const [exportType, setExportType] = useState(catalog[0]?.key ?? "crm");
  const definition = useMemo(
    () => catalog.find((item) => item.key === exportType),
    [catalog, exportType],
  );
  const [columns, setColumns] = useState<string[]>(
    definition?.defaultColumns.map((c) => c.key) ?? [],
  );
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function toggleColumn(key: string) {
    setColumns((prev) =>
      prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key],
    );
  }

  async function submit() {
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/api/exports", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          exportType,
          columns,
          dateFrom: dateFrom || undefined,
          dateTo: dateTo || undefined,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        setMessage(data.error ?? "Export failed");
        return;
      }
      setMessage(
        data.job.requiresApproval
          ? `Export ${data.job.id} awaiting approval`
          : `Export ${data.job.id} · ${data.job.status}`,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Request export</CardTitle>
        <CardDescription>
          Server-side permission filtering applies to every column. Large jobs
          generate in the background with expiring download links.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <label className="block text-sm">
          <span className="mb-1 block text-[var(--muted)]">Dataset</span>
          <select
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
            value={exportType}
            onChange={(e) => {
              const next = e.target.value as typeof exportType;
              setExportType(next);
              const def = catalog.find((item) => item.key === next);
              setColumns(def?.defaultColumns.map((c) => c.key) ?? []);
            }}
          >
            {catalog.map((item) => (
              <option key={item.key} value={item.key}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        {definition ? (
          <p className="text-sm text-[var(--muted)]">
            {definition.description}
            {definition.requiresApproval
              ? " Sensitive exports require approval."
              : ""}
          </p>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--muted)]">From</span>
            <input
              type="date"
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--muted)]">To</span>
            <input
              type="date"
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
        </div>

        <fieldset>
          <legend className="mb-2 text-sm text-[var(--muted)]">
            Visible columns
          </legend>
          <div className="flex flex-wrap gap-3">
            {definition?.defaultColumns.map((col) => (
              <label key={col.key} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={columns.includes(col.key)}
                  onChange={() => toggleColumn(col.key)}
                />
                {col.label}
                {col.sensitive ? " (sensitive)" : ""}
              </label>
            ))}
          </div>
        </fieldset>

        <Button type="button" disabled={busy || columns.length === 0} onClick={submit}>
          {busy ? "Queuing…" : "Queue export"}
        </Button>
        {message ? <p className="text-sm">{message}</p> : null}
      </CardContent>
    </Card>
  );
}
