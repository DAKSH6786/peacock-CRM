"use client";

import { ReportViewer } from "@/components/reports/report-viewer";
import { useBrowserStorageValue } from "@/lib/browser-storage-store";
import type { ReportPayload } from "@/modules/reports/types";

function readPreview(): ReportPayload | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem("peacock:builder-preview");
    if (!raw) return null;
    return JSON.parse(raw) as ReportPayload;
  } catch {
    return null;
  }
}

export default function BuilderPreviewClient({ canExport }: { canExport: boolean }) {
  const payload = useBrowserStorageValue(readPreview, null);

  if (!payload) {
    return (
      <p className="text-sm text-[var(--muted)]">
        No preview loaded. Build a report and choose Preview.
      </p>
    );
  }

  return <ReportViewer payload={payload} canExport={canExport} />;
}
