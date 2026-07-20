"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { LeadForm } from "@/components/crm/lead-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type LeadDetail = {
  id: string;
  personName: string;
  companyName: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  city: string | null;
  website: string | null;
  estimatedValueMinor: number | null;
  currencyCode: string;
  probability: number | null;
  leadScore: number;
  scoreBreakdown: unknown;
  lastContactedAt: string | null;
  nextFollowUpAt: string | null;
  notes: string | null;
  companySize: string | null;
  budgetMinor: number | null;
  decisionTimeline: string | null;
  websiteQuality: number | null;
  existingRelationship: boolean;
  interestedServices: unknown;
  sourceId: string | null;
  statusId: string | null;
  pipelineId: string | null;
  stageId: string | null;
  assignedUserId: string | null;
  source?: { name: string } | null;
  status?: { name: string } | null;
  stage?: { name: string } | null;
  assignedUser?: { name: string | null; email: string } | null;
  company?: { id: string; name: string } | null;
  contact?: { id: string; firstName: string; lastName: string | null } | null;
  activities: Array<{
    id: string;
    type: string;
    subject: string | null;
    body: string | null;
    occurredAt: string;
  }>;
  callLogs: Array<{
    id: string;
    direction: string;
    outcome: string | null;
    notes: string | null;
    occurredAt: string;
  }>;
  meetings: Array<{
    id: string;
    title: string;
    startsAt: string;
    location: string | null;
  }>;
  notesList: Array<{ id: string; body: string; createdAt: string }>;
  emailActivities: Array<{
    id: string;
    direction: string;
    subject: string | null;
    occurredAt: string;
  }>;
  followUps: Array<{
    id: string;
    dueAt: string;
    completedAt: string | null;
    notes: string | null;
  }>;
  stageHistory: Array<{
    id: string;
    createdAt: string;
    note: string | null;
    toStage: { name: string };
  }>;
  assignmentHistory: Array<{
    id: string;
    createdAt: string;
    fromUserId: string | null;
    toUserId: string | null;
    reason: string | null;
  }>;
  deals: Array<{ id: string; name: string; valueMinor: number }>;
  leadTags: Array<{ tag: { id: string; name: string } }>;
};

type Lookups = {
  sources: Array<{ id: string; name: string }>;
  statuses: Array<{ id: string; name: string }>;
  pipelines: Array<{
    id: string;
    name: string;
    stages: Array<{ id: string; name: string }>;
  }>;
  users: Array<{ id: string; name: string | null; email: string }>;
  tags: Array<{ id: string; name: string }>;
  lostReasons: Array<{ id: string; name: string }>;
};

type Props = {
  lead: LeadDetail;
  lookups: Lookups;
  canManage: boolean;
  startInEdit?: boolean;
};

export function LeadDetailView({
  lead,
  lookups,
  canManage,
  startInEdit,
}: Props) {
  const router = useRouter();
  const [editing, setEditing] = useState(Boolean(startInEdit));
  const [message, setMessage] = useState<string | null>(null);
  const [activityType, setActivityType] = useState("NOTE");
  const [activityBody, setActivityBody] = useState("");
  const [followUpAt, setFollowUpAt] = useState("");

  async function postAction(payload: Record<string, unknown>) {
    const response = await fetch(`/api/crm/leads/${lead.id}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error ?? "Action failed");
      return;
    }
    setMessage("Saved");
    router.refresh();
  }

  const breakdown = Array.isArray(lead.scoreBreakdown)
    ? (lead.scoreBreakdown as Array<{
        label: string;
        points: number;
        reason: string;
      }>)
    : [];

  if (editing && canManage) {
    return (
      <div className="space-y-4">
        <Button type="button" variant="secondary" onClick={() => setEditing(false)}>
          Cancel edit
        </Button>
        <LeadForm mode="edit" lookups={lookups} initial={lead} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {canManage ? (
          <>
            <Button type="button" onClick={() => setEditing(true)}>
              Edit
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() =>
                void postAction({
                  action: "convert",
                  createContact: true,
                  createCompany: true,
                  createDeal: true,
                  createClientAccount: true,
                  createProjectPlaceholder: false,
                })
              }
            >
              Convert to client
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void postAction({ action: "create-quote" })}
            >
              Generate quote
            </Button>
          </>
        ) : null}
        <Button asChild variant="secondary">
          <Link href="/crm/pipeline">Pipeline</Link>
        </Button>
      </div>
      {message ? <p className="text-sm">{message}</p> : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Summary</CardTitle>
            <CardDescription>
              {lead.status?.name ?? "No status"} · {lead.stage?.name ?? "No stage"} ·
              Score {lead.leadScore}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 text-sm">
            <div>
              <p className="text-[var(--muted)]">Contact</p>
              <p>{lead.email ?? "—"}</p>
              <p>{lead.phone ?? "—"}</p>
              <p>
                {[lead.city, lead.country].filter(Boolean).join(", ") || "—"}
              </p>
            </div>
            <div>
              <p className="text-[var(--muted)]">Company</p>
              <p>{lead.companyName ?? lead.company?.name ?? "—"}</p>
              <p>{lead.website ?? "—"}</p>
              <p>Size: {lead.companySize ?? "—"}</p>
            </div>
            <div>
              <p className="text-[var(--muted)]">Deal value</p>
              <p>
                {lead.currencyCode}{" "}
                {((lead.estimatedValueMinor ?? 0) / 100).toLocaleString()}
              </p>
              <p>Probability {lead.probability ?? "—"}%</p>
              <p>
                Budget{" "}
                {lead.budgetMinor != null
                  ? (lead.budgetMinor / 100).toLocaleString()
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-[var(--muted)]">Qualification</p>
              <p>Source: {lead.source?.name ?? "—"}</p>
              <p>Owner: {lead.assignedUser?.name ?? lead.assignedUser?.email ?? "—"}</p>
              <p>Timeline: {lead.decisionTimeline ?? "—"}</p>
              <p>
                Relationship:{" "}
                {lead.existingRelationship ? "Existing" : "New"}
              </p>
            </div>
            <div className="sm:col-span-2">
              <p className="text-[var(--muted)]">Interested services</p>
              <p>
                {Array.isArray(lead.interestedServices)
                  ? lead.interestedServices.join(", ") || "—"
                  : "—"}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {lead.leadTags.map((t) => (
                  <Badge key={t.tag.id} tone="default">
                    {t.tag.name}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lead score</CardTitle>
            <CardDescription>Transparent rule-based breakdown</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="text-3xl font-semibold">{lead.leadScore}</p>
            {breakdown.length === 0 ? (
              <p className="text-[var(--muted)]">No scoring factors matched.</p>
            ) : (
              breakdown.map((item, index) => (
                <div key={`${item.label}-${index}`}>
                  <p className="font-medium">
                    +{item.points} {item.label}
                  </p>
                  <p className="text-xs text-[var(--muted)]">{item.reason}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {canManage ? (
        <Card>
          <CardHeader>
            <CardTitle>Log activity / follow-up</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <select
                className="w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                value={activityType}
                onChange={(e) => setActivityType(e.target.value)}
              >
                <option value="NOTE">Note</option>
                <option value="CALL">Call</option>
                <option value="MEETING">Meeting</option>
                <option value="EMAIL">Email</option>
              </select>
              <textarea
                className="min-h-24 w-full rounded-md border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm"
                placeholder="Details / outcome / @mention teammates"
                value={activityBody}
                onChange={(e) => setActivityBody(e.target.value)}
              />
              <Button
                type="button"
                onClick={() =>
                  void postAction({
                    action: "activity",
                    type: activityType,
                    body: activityBody,
                    subject: activityType,
                    direction: "OUTBOUND",
                  })
                }
              >
                Save activity
              </Button>
            </div>
            <div className="space-y-2">
              <Input
                type="datetime-local"
                value={followUpAt}
                onChange={(e) => setFollowUpAt(e.target.value)}
              />
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  void postAction({
                    action: "follow-up",
                    dueAt: new Date(followUpAt).toISOString(),
                    notes: "Scheduled from lead detail",
                  })
                }
              >
                Create follow-up
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <HistoryCard
          title="Activities"
          items={lead.activities.map((a) => ({
            id: a.id,
            title: `${a.type}${a.subject ? ` · ${a.subject}` : ""}`,
            meta: a.occurredAt.slice(0, 16),
            body: a.body,
          }))}
        />
        <HistoryCard
          title="Notes"
          items={lead.notesList.map((n) => ({
            id: n.id,
            title: "Note",
            meta: n.createdAt.slice(0, 16),
            body: n.body,
          }))}
        />
        <HistoryCard
          title="Calls"
          items={lead.callLogs.map((c) => ({
            id: c.id,
            title: `${c.direction}${c.outcome ? ` · ${c.outcome}` : ""}`,
            meta: c.occurredAt.slice(0, 16),
            body: c.notes,
          }))}
        />
        <HistoryCard
          title="Meetings"
          items={lead.meetings.map((m) => ({
            id: m.id,
            title: m.title,
            meta: m.startsAt.slice(0, 16),
            body: m.location,
          }))}
        />
        <HistoryCard
          title="Emails"
          items={lead.emailActivities.map((e) => ({
            id: e.id,
            title: `${e.direction} · ${e.subject ?? "(no subject)"}`,
            meta: e.occurredAt.slice(0, 16),
            body: null,
          }))}
        />
        <Card>
          <CardHeader>
            <CardTitle>Follow-ups</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {lead.followUps.length === 0 ? (
              <p className="text-[var(--muted)]">No follow-ups.</p>
            ) : (
              lead.followUps.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center justify-between gap-2 border-b border-[var(--border)] pb-2"
                >
                  <div>
                    <p>{f.dueAt.slice(0, 16)}</p>
                    <p className="text-xs text-[var(--muted)]">{f.notes}</p>
                  </div>
                  {canManage && !f.completedAt ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() =>
                        void postAction({
                          action: "complete-follow-up",
                          followUpId: f.id,
                        })
                      }
                    >
                      Complete
                    </Button>
                  ) : (
                    <Badge tone="default">Done</Badge>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <HistoryCard
          title="Stage history"
          items={lead.stageHistory.map((s) => ({
            id: s.id,
            title: s.toStage.name,
            meta: s.createdAt.slice(0, 16),
            body: s.note,
          }))}
        />
        <HistoryCard
          title="Assignment history"
          items={lead.assignmentHistory.map((a) => ({
            id: a.id,
            title: a.reason ?? "Reassigned",
            meta: a.createdAt.slice(0, 16),
            body: `${a.fromUserId ?? "—"} → ${a.toUserId ?? "—"}`,
          }))}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Linked deals / conversion</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-1">
          <p>Contact: {lead.contact ? `${lead.contact.firstName} ${lead.contact.lastName ?? ""}` : "Not converted"}</p>
          <p>Company: {lead.company?.name ?? "Not converted"}</p>
          {lead.deals.map((d) => (
            <p key={d.id}>
              Deal: {d.name} · {(d.valueMinor / 100).toLocaleString()}
            </p>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function HistoryCard({
  title,
  items,
}: {
  title: string;
  items: Array<{
    id: string;
    title: string;
    meta: string;
    body?: string | null;
  }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="max-h-64 space-y-2 overflow-auto text-sm">
        {items.length === 0 ? (
          <p className="text-[var(--muted)]">None yet.</p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="border-b border-[var(--border)] pb-2">
              <p className="font-medium">{item.title}</p>
              <p className="text-xs text-[var(--muted)]">{item.meta}</p>
              {item.body ? <p className="mt-1">{item.body}</p> : null}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
