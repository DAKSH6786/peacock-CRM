"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { ReportDateFilter } from "@/components/reports/report-controls";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BUILDER_DATASETS } from "@/modules/reports/builder/datasets";

type Dataset = (typeof BUILDER_DATASETS)[number];

export function ReportBuilderForm({
  allowedDatasetIds,
  from,
  to,
}: {
  allowedDatasetIds: string[];
  from: string;
  to: string;
}) {
  const router = useRouter();
  const datasets = useMemo(
    () => BUILDER_DATASETS.filter((dataset) => allowedDatasetIds.includes(dataset.id)),
    [allowedDatasetIds],
  );
  const [datasetId, setDatasetId] = useState<string>(datasets[0]?.id ?? "leads");
  const dataset = datasets.find((item) => item.id === datasetId) as Dataset | undefined;
  const [groupBy, setGroupBy] = useState<string>(dataset?.fields[0]?.id ?? "source");
  const [measure, setMeasure] = useState<string>(dataset?.measures[0]?.id ?? "count");
  const [chartType, setChartType] = useState<"bar" | "line" | "table">("bar");
  const [name, setName] = useState("My custom report");
  const [shareRoles, setShareRoles] = useState<string[]>([]);
  const [cadence, setCadence] = useState<"none" | "daily" | "weekly" | "monthly">("none");
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  if (!dataset) {
    return <p className="text-sm text-[var(--muted)]">No datasets available for your role.</p>;
  }

  const definition = {
    datasetId: datasetId as Dataset["id"],
    fields: dataset.fields.map((field) => field.id),
    filters: [],
    groupBy: [groupBy],
    measures: [measure],
    chartType,
  };

  return (
    <div className="space-y-6">
      <ReportDateFilter from={from} to={to} />

      <Card>
        <CardHeader>
          <CardTitle>Constrained builder</CardTitle>
          <CardDescription>
            Choose an approved dataset, fields, measures, and chart type. Arbitrary SQL is not allowed.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="dataset">Dataset</Label>
            <select
              id="dataset"
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 text-sm"
              value={datasetId}
              onChange={(event) => {
                const next = event.target.value;
                setDatasetId(next);
                const found = datasets.find((item) => item.id === next);
                setGroupBy(found?.fields[0]?.id ?? "");
                setMeasure(found?.measures[0]?.id ?? "");
              }}
            >
              {datasets.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="groupBy">Group by</Label>
            <select
              id="groupBy"
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 text-sm"
              value={groupBy}
              onChange={(event) => setGroupBy(event.target.value)}
            >
              {dataset.fields.map((field) => (
                <option key={field.id} value={field.id}>
                  {field.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="measure">Measure</Label>
            <select
              id="measure"
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 text-sm"
              value={measure}
              onChange={(event) => setMeasure(event.target.value)}
            >
              {dataset.measures.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="chartType">Chart type</Label>
            <select
              id="chartType"
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 text-sm"
              value={chartType}
              onChange={(event) =>
                setChartType(event.target.value as "bar" | "line" | "table")
              }
            >
              <option value="bar">Bar</option>
              <option value="line">Line</option>
              <option value="table">Table</option>
            </select>
          </div>

          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="name">Save as</Label>
            <Input
              id="name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Share with roles</Label>
            <div className="flex flex-wrap gap-2 text-sm">
              {["MANAGER", "SALES", "FINANCE", "HR"].map((role) => {
                const checked = shareRoles.includes(role);
                return (
                  <label key={role} className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() =>
                        setShareRoles((current) =>
                          checked
                            ? current.filter((item) => item !== role)
                            : [...current, role],
                        )
                      }
                    />
                    {role}
                  </label>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="cadence">Schedule export</Label>
            <select
              id="cadence"
              className="h-10 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 text-sm"
              value={cadence}
              onChange={(event) =>
                setCadence(event.target.value as typeof cadence)
              }
            >
              <option value="none">No schedule</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button
          disabled={pending}
          onClick={() => {
            startTransition(() => {
              void (async () => {
                const params = new URLSearchParams({ from, to });
                const response = await fetch(
                  `/api/reports/builder/preview?${params.toString()}`,
                  {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ definition }),
                  },
                );
                if (!response.ok) {
                  setMessage("Preview failed");
                  return;
                }
                const payload = await response.json();
                sessionStorage.setItem(
                  "peacock:builder-preview",
                  JSON.stringify(payload),
                );
                router.push(`/reports/builder/preview?${params.toString()}`);
              })();
            });
          }}
        >
          {pending ? "Running…" : "Preview"}
        </Button>
        <Button
          variant="secondary"
          disabled={pending || !name.trim()}
          onClick={() => {
            startTransition(() => {
              void (async () => {
                const response = await fetch("/api/reports/builder", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    name,
                    definition,
                    chartType,
                    shareRoles,
                    schedule:
                      cadence === "none"
                        ? undefined
                        : { cadence, format: "csv" },
                  }),
                });
                if (!response.ok) {
                  setMessage("Save failed");
                  return;
                }
                setMessage("Saved");
                router.push("/reports/saved");
              })();
            });
          }}
        >
          Save report
        </Button>
      </div>
      {message ? <p className="text-sm text-[var(--muted)]">{message}</p> : null}
    </div>
  );
}
