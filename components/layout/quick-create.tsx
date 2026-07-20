"use client";

import Link from "next/link";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Plus } from "lucide-react";

import { quickCreateItems } from "@/components/layout/nav-config";
import { Button } from "@/components/ui/button";
import { hasPermission } from "@/permissions/types";

export function QuickCreateMenu({ role }: { role: string | null }) {
  const items = quickCreateItems.filter(
    (item) => !item.permission || hasPermission(role as never, item.permission),
  );

  if (items.length === 0) return null;

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button size="sm" aria-label="Quick create">
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">Create</span>
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 min-w-44 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-1 shadow-[var(--shadow-soft)]"
        >
          {items.map((item) => (
            <DropdownMenu.Item key={item.href} asChild>
              <Link
                href={item.href}
                className="block rounded-xl px-3 py-2 text-sm outline-none hover:bg-[var(--surface-hover)] focus:bg-[var(--surface-hover)]"
              >
                {item.label}
              </Link>
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
