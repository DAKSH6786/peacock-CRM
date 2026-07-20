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
import type { ImportEntityDefinition } from "@/modules/imports";

type Props = {
  catalog: ImportEntityDefinition[];
};

export function ImportWorkflowPanel({ catalog }: Props) {
  const [entityType, setEntityType] = useState(catalog[0]?.key ?? "leads");
  const [csvText, setCsvText] = useState("");
  const [fileName, setFileName] = useState("import.csv");
  const [duplicatePolicy, setDuplicatePolicy] = useState("SKIP");
  const [partialPolicy, setPartialPolicy] = useState("COMMIT_VALID");
  const [message, setMessage] = useState<string | null>(null);
  const [preview, setPreview] = useState<Record<string, string>[]>([]);
  const [errors, setErrors] = useState<
    Array<{ row: number; field?: string; message: string }>
  >([]);
  const [busy, setBusy] = useState(false);

  const definition = useMemo(
    () => catalog.find((item) => item.key === entityType),
    [catalog, entityType],
  );

  async function downloadTemplate() {
    const response = await fetch("/api/imports", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ entityType, templateOnly: true }),
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${entityType}-template.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function runImport() {
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/api/imports", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          entityType,
          csvText,
          fileName,
          duplicatePolicy,
          partialPolicy,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        setErrors(data.validation?.errors ?? []);
        setPreview(data.preview ?? []);
        setMessage(data.error ?? "Import failed");
        return;
      }
      setErrors(data.validation?.errors ?? []);
      setPreview(data.preview ?? []);
      setMessage(`Import job ${data.job.id} · ${data.job.status}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>New import</CardTitle>
        <CardDescription>
          Map columns from the CSV template, preview rows, then queue background
          processing with a partial-import policy.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <label className="block text-sm">
          <span className="mb-1 block text-[var(--muted)]">Entity</span>
          <select
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value as typeof entityType)}
          >
            {catalog.map((item) => (
              <option key={item.key} value={item.key}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        {definition ? (
          <p className="text-sm text-[var(--muted)]">{definition.description}</p>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={downloadTemplate}>
            Download template
          </Button>
        </div>

        <label className="block text-sm">
          <span className="mb-1 block text-[var(--muted)]">CSV file</span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              setFileName(file.name);
              setCsvText(await file.text());
            }}
          />
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--muted)]">Duplicates</span>
            <select
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
              value={duplicatePolicy}
              onChange={(e) => setDuplicatePolicy(e.target.value)}
            >
              <option value="SKIP">Skip duplicates</option>
              <option value="UPDATE">Update duplicates</option>
              <option value="FAIL">Fail on duplicates</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-[var(--muted)]">Partial import</span>
            <select
              className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2"
              value={partialPolicy}
              onChange={(e) => setPartialPolicy(e.target.value)}
            >
              <option value="COMMIT_VALID">Commit valid rows</option>
              <option value="ALL_OR_NOTHING">All or nothing</option>
            </select>
          </label>
        </div>

        <Button type="button" disabled={!csvText || busy} onClick={runImport}>
          {busy ? "Validating…" : "Validate & import"}
        </Button>

        {message ? <p className="text-sm">{message}</p> : null}

        {preview.length > 0 ? (
          <div>
            <p className="mb-2 text-sm font-medium">Preview</p>
            <pre className="max-h-48 overflow-auto rounded-md bg-[var(--surface-2)] p-3 text-xs">
              {JSON.stringify(preview.slice(0, 5), null, 2)}
            </pre>
          </div>
        ) : null}

        {errors.length > 0 ? (
          <div>
            <p className="mb-2 text-sm font-medium">Validation errors</p>
            <ul className="max-h-40 space-y-1 overflow-auto text-xs text-[var(--danger)]">
              {errors.slice(0, 30).map((err, index) => (
                <li key={`${err.row}-${err.field}-${index}`}>
                  Row {err.row}
                  {err.field ? ` · ${err.field}` : ""}: {err.message}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
