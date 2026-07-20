"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type Card = {
  id: string;
  personName: string;
  companyName: string | null;
  estimatedValueMinor: number | null;
  currencyCode: string;
  leadScore: number;
  probability: number;
  ageDays: number;
  stale: boolean;
  assignedUser: { id: string; name: string | null; email: string } | null;
  tags: Array<{ id: string; name: string }>;
};

type Column = {
  stage: {
    id: string;
    name: string;
    color: string | null;
    probability: number;
    requiredFields: string[];
    isClosedWon: boolean;
    isClosedLost: boolean;
    staleAfterDays: number | null;
  };
  cards: Card[];
  totalValueMinor: number;
  weightedValueMinor: number;
};

type Props = {
  initialColumns: Column[];
  pipelineName: string;
  lostReasons: Array<{ id: string; name: string }>;
  canManage: boolean;
};

function money(minor: number, currency = "INR") {
  return `${currency} ${(minor / 100).toLocaleString()}`;
}

export function PipelineKanban({
  initialColumns,
  pipelineName,
  lostReasons,
  canManage,
}: Props) {
  const [columns, setColumns] = useState(initialColumns);
  const [dragLeadId, setDragLeadId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pendingClose, setPendingClose] = useState<{
    leadId: string;
    stageId: string;
    isLost: boolean;
  } | null>(null);
  const [lostReasonId, setLostReasonId] = useState("");

  function findCard(leadId: string) {
    for (const col of columns) {
      const card = col.cards.find((c) => c.id === leadId);
      if (card) return { card, fromStageId: col.stage.id };
    }
    return null;
  }

  function optimisticMove(leadId: string, toStageId: string) {
    const found = findCard(leadId);
    if (!found) return null;
    const snapshot = structuredClone(columns);
    setColumns((prev) => {
      const next = prev.map((col) => ({
        ...col,
        cards: col.cards.filter((c) => c.id !== leadId),
      }));
      return next.map((col) => {
        if (col.stage.id !== toStageId) return col;
        return {
          ...col,
          cards: [
            {
              ...found.card,
              probability: col.stage.probability,
            },
            ...col.cards,
          ],
        };
      });
    });
    return snapshot;
  }

  async function commitMove(
    leadId: string,
    stageId: string,
    options?: { confirmClose?: boolean; lostReasonId?: string },
  ) {
    const target = columns.find((c) => c.stage.id === stageId)?.stage;
    if (
      target &&
      (target.isClosedWon || target.isClosedLost) &&
      !options?.confirmClose
    ) {
      setPendingClose({
        leadId,
        stageId,
        isLost: target.isClosedLost,
      });
      return;
    }

    const snapshot = optimisticMove(leadId, stageId);
    const response = await fetch("/api/crm/pipeline", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        leadId,
        stageId,
        confirmClose: options?.confirmClose ?? false,
        lostReasonId: options?.lostReasonId,
      }),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      if (snapshot) setColumns(snapshot);
      if (data.reason === "REQUIRED_FIELDS") {
        setMessage(
          `Missing required fields: ${(data.missingFields ?? []).join(", ")}`,
        );
      } else if (data.reason === "CONFIRM_CLOSE") {
        setPendingClose({
          leadId,
          stageId,
          isLost: Boolean(data.stage?.isClosedLost),
        });
      } else if (data.reason === "LOST_REASON_REQUIRED") {
        setMessage("Lost reason is required");
        setPendingClose({ leadId, stageId, isLost: true });
      } else {
        setMessage(data.error ?? "Move failed — rolled back");
      }
      return;
    }
    setMessage(null);
    setPendingClose(null);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-[var(--muted)]">Pipeline: {pipelineName}</p>
        {message ? <p className="text-sm text-[var(--danger)]">{message}</p> : null}
      </div>

      {pendingClose ? (
        <div className="rounded-md border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <p className="mb-2 text-sm font-medium">
            Confirm closing this lead as{" "}
            {pendingClose.isLost ? "lost" : "won"}?
          </p>
          {pendingClose.isLost ? (
            <select
              className="mb-3 w-full max-w-sm rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
              value={lostReasonId}
              onChange={(e) => setLostReasonId(e.target.value)}
            >
              <option value="">Select lost reason</option>
              {lostReasons.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          ) : null}
          <div className="flex gap-2">
            <Button
              type="button"
              onClick={() =>
                void commitMove(pendingClose.leadId, pendingClose.stageId, {
                  confirmClose: true,
                  lostReasonId: lostReasonId || undefined,
                })
              }
            >
              Confirm
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setPendingClose(null)}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : null}

      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((column) => (
          <div
            key={column.stage.id}
            className="w-72 shrink-0 rounded-lg border border-[var(--border)] bg-[var(--surface)]"
            onDragOver={(e) => {
              if (canManage) e.preventDefault();
            }}
            onDrop={(e) => {
              e.preventDefault();
              if (!canManage || !dragLeadId) return;
              void commitMove(dragLeadId, column.stage.id);
              setDragLeadId(null);
            }}
          >
            <div
              className="rounded-t-lg px-3 py-2"
              style={{
                borderTop: `3px solid ${column.stage.color ?? "var(--accent)"}`,
              }}
            >
              <div className="flex items-center justify-between">
                <p className="font-medium">{column.stage.name}</p>
                <Badge tone="default">{column.cards.length}</Badge>
              </div>
              <p className="text-xs text-[var(--muted)]">
                {column.stage.probability}% · {money(column.totalValueMinor)} ·
                wtd {money(column.weightedValueMinor)}
              </p>
            </div>
            <div className="space-y-2 p-2">
              {column.cards.map((card) => (
                <div
                  key={card.id}
                  draggable={canManage}
                  onDragStart={() => setDragLeadId(card.id)}
                  className="cursor-grab rounded-md border border-[var(--border)] bg-[var(--background)] p-3 active:cursor-grabbing"
                >
                  <Link
                    href={`/crm/leads/${card.id}`}
                    className="font-medium hover:underline"
                  >
                    {card.personName}
                  </Link>
                  <p className="text-xs text-[var(--muted)]">
                    {card.companyName ?? "No company"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {card.stale ? <Badge tone="default">Stale</Badge> : null}
                    <Badge tone="default">Score {card.leadScore}</Badge>
                    <Badge tone="default">{card.ageDays}d</Badge>
                  </div>
                  <p className="mt-2 text-xs">
                    {money(card.estimatedValueMinor ?? 0, card.currencyCode)} ·{" "}
                    {card.assignedUser?.name ??
                      card.assignedUser?.email ??
                      "Unassigned"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
