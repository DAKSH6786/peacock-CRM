import { StatusBadge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function CommentPanel({
  comments,
}: {
  comments: Array<{ id: string; author: string; body: string; at: string }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Comments</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {comments.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No comments yet.</p>
        ) : (
          comments.map((comment) => (
            <article
              key={comment.id}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3"
            >
              <header className="mb-1 flex items-center justify-between gap-2">
                <p className="text-sm font-semibold">{comment.author}</p>
                <time className="text-xs text-[var(--muted)]">
                  {comment.at}
                </time>
              </header>
              <p className="text-sm text-[var(--foreground)]">{comment.body}</p>
            </article>
          ))
        )}
      </CardContent>
    </Card>
  );
}

export function FileAttachmentList({
  files,
}: {
  files: Array<{ id: string; name: string; sizeLabel: string }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Attachments</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {files.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No files attached.</p>
        ) : (
          <ul className="space-y-2">
            {files.map((file) => (
              <li
                key={file.id}
                className="flex items-center justify-between rounded-xl border border-[var(--border)] px-3 py-2 text-sm"
              >
                <span className="font-medium">{file.name}</span>
                <span className="text-[var(--muted)]">{file.sizeLabel}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export function ApprovalPanel({
  items,
}: {
  items: Array<{ id: string; title: string; status: string }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Approvals</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between gap-3 rounded-xl border border-[var(--border)] px-3 py-2"
          >
            <p className="text-sm font-medium">{item.title}</p>
            <StatusBadge status={item.status} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function AuditHistoryPanel({
  entries,
}: {
  entries: Array<{ id: string; action: string; actor: string; at: string }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit history</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="rounded-xl border border-[var(--border)] px-3 py-2 text-sm"
          >
            <p className="font-medium">{entry.action}</p>
            <p className="text-[var(--muted)]">
              {entry.actor} · {entry.at}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
