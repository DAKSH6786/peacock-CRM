"use client";

import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useBrowserStorageValue } from "@/lib/browser-storage-store";
import { getRecentlyViewed } from "@/lib/recent-records";
import type {
  MyWorkItem,
  MyWorkPayload,
} from "@/modules/dashboard/my-work.types";

type Section = {
  id: string;
  title: string;
  description: string;
  items: MyWorkItem[];
  empty: string;
};

function WorkSection({ section }: { section: Section }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{section.title}</CardTitle>
        <CardDescription>{section.description}</CardDescription>
      </CardHeader>
      <CardContent>
        {section.items.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">{section.empty}</p>
        ) : (
          <ul className="divide-y divide-[var(--border)]">
            {section.items.map((item) => (
              <li key={item.id} className="py-3 first:pt-0 last:pb-0">
                <Link
                  href={item.href}
                  className="text-sm font-semibold text-[var(--accent-teal)] hover:underline"
                >
                  {item.title}
                </Link>
                {item.meta ? (
                  <p className="mt-0.5 text-xs text-[var(--muted)]">
                    {item.meta}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export function MyWorkView({ payload }: { payload: MyWorkPayload }) {
  const recent = useBrowserStorageValue(getRecentlyViewed, []);

  const sections: Section[] = [
    {
      id: "tasks",
      title: "Tasks assigned to me",
      description: "Open work items on your plate.",
      items: payload.tasks,
      empty: "No open tasks assigned to you.",
    },
    {
      id: "deliverables",
      title: "Deliverables awaiting my action",
      description: "Reviews waiting on your decision.",
      items: payload.deliverables,
      empty: "No deliverables need your review.",
    },
    {
      id: "follow-ups",
      title: "Leads requiring follow-up",
      description: "CRM follow-ups due or overdue.",
      items: payload.leadFollowUps,
      empty: "No lead follow-ups waiting.",
    },
    {
      id: "approvals",
      title: "Approval requests",
      description: "Items you requested or must decide.",
      items: payload.approvals,
      empty: "No pending approval requests.",
    },
    {
      id: "xyme",
      title: "XYME goals",
      description: "Active goals on your current plan.",
      items: payload.xymeGoals,
      empty: "No active XYME goals.",
    },
    {
      id: "check-ins",
      title: "Check-in reminders",
      description: "Plans that still need a weekly check-in.",
      items: payload.checkInReminders,
      empty: "You are up to date on check-ins.",
    },
    {
      id: "attendance",
      title: "Attendance exceptions",
      description: "Corrections awaiting resolution.",
      items: payload.attendanceExceptions,
      empty: "No attendance exceptions.",
    },
    {
      id: "announcements",
      title: "Unread announcements",
      description: "Latest company announcements.",
      items: payload.announcements,
      empty: "No announcements right now.",
    },
  ];

  const totalItems = sections.reduce(
    (sum, section) => sum + section.items.length,
    0,
  );

  return (
    <div>
      <PageHeader
        title="My Work"
        description="Your personal queue across tasks, approvals, follow-ups, and goals."
        actions={
          <Button asChild variant="secondary">
            <Link href="/dashboard">Back to dashboard</Link>
          </Button>
        }
      />

      {totalItems === 0 && recent.length === 0 ? (
        <EmptyState
          title="Your queue is clear"
          description="When tasks, follow-ups, approvals, or announcements land on your desk, they will show up here."
        />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {sections.map((section) => (
            <WorkSection key={section.id} section={section} />
          ))}

          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Recently viewed records</CardTitle>
              <CardDescription>
                Stored on this device from universal search navigation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recent.length === 0 ? (
                <p className="text-sm text-[var(--muted)]">
                  Open a search result with ⌘K / Ctrl+K to build this list.
                </p>
              ) : (
                <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {recent.map((item) => (
                    <li key={`${item.href}-${item.id}`}>
                      <Link
                        href={item.href}
                        className="block rounded-xl border border-[var(--border)] px-3 py-2 hover:bg-[var(--accent-soft)]"
                      >
                        <p className="text-sm font-semibold">{item.title}</p>
                        <p className="mt-0.5 text-xs text-[var(--muted)]">
                          {item.category ?? item.subtitle ?? item.href}
                        </p>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
