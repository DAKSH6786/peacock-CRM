"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Building2, ChevronsUpDown } from "lucide-react";

import { Button } from "@/components/ui/button";

export function OrganizationSwitcher() {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="hidden gap-2 md:inline-flex"
          aria-label="Organization switcher"
        >
          <Building2 className="h-4 w-4 text-[var(--accent-teal)]" />
          <span className="max-w-[10rem] truncate">Digital Peacock</span>
          <ChevronsUpDown className="h-3.5 w-3.5 text-[var(--muted)]" />
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={8}
          className="z-50 w-64 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[var(--shadow-soft)]"
        >
          <p className="px-2 py-1 text-xs font-semibold tracking-wide text-[var(--muted)] uppercase">
            Organization
          </p>
          <DropdownMenu.Item className="rounded-xl bg-[var(--accent-soft)] px-3 py-2 text-sm font-medium text-[var(--accent-teal)] outline-none">
            Digital Peacock
          </DropdownMenu.Item>
          <p className="mt-2 px-2 py-1 text-xs text-[var(--muted)]">
            Multi-organization switching will be enabled in a later release.
          </p>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
