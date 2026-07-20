"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Bell } from "lucide-react";

import { Button } from "@/components/ui/button";

const DEMO_NOTIFICATIONS = [
  {
    id: "1",
    title: "Leave request awaiting review",
    body: "A team member submitted leave for next week.",
    time: "12m ago",
  },
  {
    id: "2",
    title: "Invoice payment received",
    body: "Finance recorded a new client payment.",
    time: "1h ago",
  },
  {
    id: "3",
    title: "XYME check-in reminder",
    body: "Q2 goals need an update before Friday.",
    time: "Yesterday",
  },
];

export function NotificationCenter() {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open notification centre"
          className="relative"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-[var(--accent-teal)]" />
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 w-80 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[var(--shadow-soft)]"
        >
          <div className="flex items-center justify-between px-2 py-2">
            <p className="text-sm font-semibold">Notifications</p>
            <span className="text-xs text-[var(--muted)]">Centre</span>
          </div>
          <ul className="space-y-1">
            {DEMO_NOTIFICATIONS.map((item) => (
              <li key={item.id}>
                <DropdownMenu.Item className="cursor-pointer rounded-xl px-3 py-2 outline-none hover:bg-[var(--surface-hover)] focus:bg-[var(--surface-hover)]">
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--muted)]">
                    {item.body}
                  </p>
                  <p className="mt-1 text-[11px] text-[var(--muted)]">
                    {item.time}
                  </p>
                </DropdownMenu.Item>
              </li>
            ))}
          </ul>
          <DropdownMenu.Item asChild>
            <a
              href="/notifications"
              className="mt-1 block rounded-xl px-3 py-2 text-center text-sm font-semibold text-[var(--accent-teal)] outline-none hover:bg-[var(--accent-soft)]"
            >
              View all
            </a>
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
