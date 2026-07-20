"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";

export function ReportExportActions({
  reportKey,
  canExport,
}: {
  reportKey: string;
  canExport: boolean;
}) {
  const searchParams = useSearchParams();
  const [busy, setBusy] = useState<string | null>(null);

  if (!canExport) return null;

  const download = async (format: "csv" | "spreadsheet" | "pdf") => {
    setBusy(format);
    try {
      const params = new URLSearchParams(searchParams.toString());
      params.set("format", format);
      const response = await fetch(
        `/api/reports/${encodeURIComponent(reportKey)}/export?${params.toString()}`,
      );
      if (!response.ok) {
        throw new Error("Export failed");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download =
        format === "pdf"
          ? `${reportKey}.html`
          : format === "spreadsheet"
            ? `${reportKey}.tsv`
            : `${reportKey}.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="secondary"
        disabled={Boolean(busy)}
        onClick={() => void download("csv")}
      >
        {busy === "csv" ? "Exporting…" : "Export CSV"}
      </Button>
      <Button
        variant="secondary"
        disabled={Boolean(busy)}
        onClick={() => void download("spreadsheet")}
      >
        {busy === "spreadsheet" ? "Exporting…" : "Export spreadsheet"}
      </Button>
      <Button
        variant="secondary"
        disabled={Boolean(busy)}
        onClick={() => void download("pdf")}
      >
        {busy === "pdf" ? "Exporting…" : "Print-friendly PDF"}
      </Button>
    </div>
  );
}
