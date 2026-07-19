import * as React from "react";

/** Highlight case-insensitive matches of `query` inside `text`. */
export function HighlightMatch({
  text,
  query,
}: {
  text: string;
  query: string;
}) {
  const q = query.trim();
  if (!q) return <>{text}</>;

  const lower = text.toLowerCase();
  const needle = q.toLowerCase();
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  let index = lower.indexOf(needle);

  while (index !== -1) {
    if (index > cursor) {
      parts.push(text.slice(cursor, index));
    }
    parts.push(
      <mark
        key={`${index}-${cursor}`}
        className="rounded-sm bg-[var(--accent-soft)] text-[var(--accent-teal)]"
      >
        {text.slice(index, index + needle.length)}
      </mark>,
    );
    cursor = index + needle.length;
    index = lower.indexOf(needle, cursor);
  }

  if (cursor < text.length) {
    parts.push(text.slice(cursor));
  }

  return <>{parts}</>;
}
