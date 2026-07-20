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
import { isPreviewableContentType } from "@/modules/documents/access";

type DocRow = {
  id: string;
  title: string;
  category: string | null;
  visibility: string;
  folderName: string | null;
  tags: string[];
  updatedAt: string;
  expiresAt: string | null;
  fileName: string | null;
  contentType: string | null;
};

type FolderRow = {
  id: string;
  name: string;
  category: string | null;
};

type Props = {
  initialDocuments: DocRow[];
  folders: FolderRow[];
  canManage: boolean;
};

export function DocumentsBrowser({
  initialDocuments,
  folders,
  canManage,
}: Props) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [documents, setDocuments] = useState(initialDocuments);

  const filtered = useMemo(() => {
    return documents.filter((doc) => {
      if (category && doc.category !== category) return false;
      if (!query) return true;
      const hay = `${doc.title} ${doc.tags.join(" ")}`.toLowerCase();
      return hay.includes(query.toLowerCase());
    });
  }, [documents, query, category]);

  async function refresh() {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (category) params.set("category", category);
    const response = await fetch(`/api/documents?${params.toString()}`);
    if (!response.ok) return;
    const data = await response.json();
    setDocuments(
      (data.documents as Array<{
        id: string;
        title: string;
        category: string | null;
        visibility: string;
        folder: { name: string } | null;
        tags: Array<{ tag: { name: string } }>;
        updatedAt: string;
        expiresAt: string | null;
        currentVersion: { fileName: string; contentType: string | null } | null;
      }>).map((doc) => ({
        id: doc.id,
        title: doc.title,
        category: doc.category,
        visibility: doc.visibility,
        folderName: doc.folder?.name ?? null,
        tags: doc.tags.map((t) => t.tag.name),
        updatedAt: doc.updatedAt,
        expiresAt: doc.expiresAt,
        fileName: doc.currentVersion?.fileName ?? null,
        contentType: doc.currentVersion?.contentType ?? null,
      })),
    );
  }

  async function onUpload(file: File) {
    const buffer = await file.arrayBuffer();
    const contentBase64 = btoa(
      String.fromCharCode(...new Uint8Array(buffer)),
    );
    const response = await fetch("/api/documents", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        action: "upload",
        title: file.name,
        fileName: file.name,
        contentType: file.type || "application/octet-stream",
        contentBase64,
        category: category || "general",
        tags: query ? [query] : [],
      }),
    });
    const data = await response.json();
    setMessage(response.ok ? `Uploaded ${data.documentId}` : data.error);
    if (response.ok) await refresh();
  }

  async function onDownload(documentId: string) {
    const response = await fetch("/api/documents", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "download", documentId }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error ?? "Download denied");
      return;
    }
    window.open(data.url, "_blank");
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.35fr_0.65fr]">
      <Card>
        <CardHeader>
          <CardTitle>Browse</CardTitle>
          <CardDescription>Search, categories, and folders.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
            placeholder="Search title or tags"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <input
            className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
            placeholder="Category filter"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
          <Button type="button" variant="secondary" onClick={refresh}>
            Apply filters
          </Button>
          <div className="space-y-2 pt-2">
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
              Folders
            </p>
            {folders.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No folders yet.</p>
            ) : (
              folders.map((folder) => (
                <p key={folder.id} className="text-sm">
                  {folder.name}
                </p>
              ))
            )}
          </div>
          {canManage ? (
            <label className="block text-sm">
              <span className="mb-1 block text-[var(--muted)]">Upload</span>
              <input
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void onUpload(file);
                }}
              />
            </label>
          ) : null}
          {message ? <p className="text-sm">{message}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>
            Preview where supported. Downloads are audited.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {filtered.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No documents match.</p>
          ) : (
            filtered.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-col gap-2 border-b border-[var(--border)] pb-3 last:border-0 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium">{doc.title}</p>
                  <p className="text-xs text-[var(--muted)]">
                    {doc.category ?? "general"} · {doc.visibility}
                    {doc.folderName ? ` · ${doc.folderName}` : ""}
                    {doc.tags.length ? ` · ${doc.tags.join(", ")}` : ""}
                    {doc.expiresAt
                      ? ` · expires ${doc.expiresAt.slice(0, 10)}`
                      : ""}
                  </p>
                </div>
                <div className="flex gap-2">
                  {isPreviewableContentType(doc.contentType) ? (
                    <span className="self-center text-xs text-[var(--muted)]">
                      Previewable
                    </span>
                  ) : null}
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => void onDownload(doc.id)}
                  >
                    Download
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
