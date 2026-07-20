"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const DEMO_APPROVALS = [
  { id: "1", title: "Expense · Creative shoot", meta: "₹24,500 · Pending" },
  { id: "2", title: "Leave · Operations", meta: "3 days · Pending" },
  { id: "3", title: "Quote · ACME rebrand", meta: "Awaiting finance" },
];

export function ApprovalInbox() {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open approval inbox"
          className="relative"
        >
          <Inbox className="h-4 w-4" />
          <Badge
            tone="warning"
            className="absolute -top-0.5 -right-0.5 h-4 min-w-4 justify-center px-1 text-[10px]"
          >
            3
          </Badge>
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 w-80 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[var(--shadow-soft)]"
        >
          <p className="px-2 py-2 text-sm font-semibold">Approval inbox</p>
          <ul className="space-y-1">
            {DEMO_APPROVALS.map((item) => (
              <li key={item.id}>
                <DropdownMenu.Item className="cursor-pointer rounded-xl px-3 py-2 outline-none hover:bg-[var(--surface-hover)] focus:bg-[var(--surface-hover)]">
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs text-[var(--muted)]">{item.meta}</p>
                </DropdownMenu.Item>
              </li>
            ))}
          </ul>
          <DropdownMenu.Item asChild>
            <a
              href="/approvals"
              className="mt-1 block rounded-xl px-3 py-2 text-center text-sm font-semibold text-[var(--accent-teal)] outline-none hover:bg-[var(--accent-soft)]"
            >
              Open approvals
            </a>
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
