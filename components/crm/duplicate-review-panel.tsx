"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";

type Candidate = {
  id: string;
  matchType: string;
  matchValue: string;
  lead: {
    id: string;
    personName: string;
    companyName: string | null;
    email: string | null;
    phone: string | null;
  };
  matchLead: {
    id: string;
    personName: string;
    companyName: string | null;
    email: string | null;
    phone: string | null;
  };
};

export function DuplicateReviewPanel({
  candidates,
  canManage,
}: {
  candidates: Candidate[];
  canManage: boolean;
}) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);

  async function dismiss(candidateId: string) {
    const response = await fetch("/api/crm/duplicates", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ candidateId, decision: "DISMISS" }),
    });
    setMessage(response.ok ? "Dismissed" : "Failed");
    router.refresh();
  }

  if (candidates.length === 0) {
    return <p className="text-sm text-[var(--muted)]">No pending duplicates.</p>;
  }

  return (
    <div className="space-y-3">
      {message ? <p className="text-sm">{message}</p> : null}
      {candidates.map((c) => (
        <div
          key={c.id}
          className="rounded-md border border-[var(--border)] p-3 text-sm"
        >
          <p className="font-medium">
            {c.matchType}: {c.matchValue}
          </p>
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            <Link href={`/crm/leads/${c.lead.id}`} className="hover:underline">
              {c.lead.personName} · {c.lead.companyName} · {c.lead.email}
            </Link>
            <Link
              href={`/crm/leads/${c.matchLead.id}`}
              className="hover:underline"
            >
              {c.matchLead.personName} · {c.matchLead.companyName} ·{" "}
              {c.matchLead.email}
            </Link>
          </div>
          {canManage ? (
            <Button
              type="button"
              size="sm"
              variant="secondary"
              className="mt-2"
              onClick={() => void dismiss(c.id)}
            >
              Keep both / dismiss
            </Button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
