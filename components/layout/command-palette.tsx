"use client";

import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import * as Dialog from "@radix-ui/react-dialog";

import {
  filterNavByRole,
  navigationSections,
  quickCreateItems,
} from "@/components/layout/nav-config";
import { useShell } from "@/components/layout/shell-context";
import { hasPermission } from "@/permissions/types";

export function CommandPalette({ role }: { role: string | null }) {
  const router = useRouter();
  const { commandOpen, setCommandOpen } = useShell();
  const sections = filterNavByRole(role, hasPermission);
  const creates = quickCreateItems.filter(
    (item) => !item.permission || hasPermission(role as never, item.permission),
  );

  const go = (href: string) => {
    setCommandOpen(false);
    router.push(href);
  };

  return (
    <Dialog.Root open={commandOpen} onOpenChange={setCommandOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/55" />
        <Dialog.Content
          className="fixed top-[18%] left-1/2 z-50 w-[min(94vw,40rem)] -translate-x-1/2 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-soft)]"
          aria-label="Command palette"
        >
          <Command className="text-[var(--foreground)]" label="Command menu">
            <div className="border-b border-[var(--border)] px-3">
              <Command.Input
                placeholder="Search pages, actions, and records…"
                className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
              />
            </div>
            <Command.List className="max-h-80 overflow-y-auto p-2">
              <Command.Empty className="px-3 py-8 text-center text-sm text-[var(--muted)]">
                No matches found.
              </Command.Empty>

              <Command.Group
                heading="Quick create"
                className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
              >
                {creates.map((item) => (
                  <Command.Item
                    key={item.href}
                    value={`create ${item.label}`}
                    onSelect={() => go(item.href)}
                    className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                  >
                    Create {item.label}
                  </Command.Item>
                ))}
              </Command.Group>

              {sections.map((section) => (
                <Command.Group
                  key={section.id}
                  heading={section.label}
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
                >
                  {section.items.map((item) => (
                    <Command.Item
                      key={`${section.id}-${item.href}-${item.label}`}
                      value={`${section.label} ${item.label}`}
                      onSelect={() => go(item.href)}
                      className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                    >
                      {item.label}
                    </Command.Item>
                  ))}
                </Command.Group>
              ))}

              <Command.Group heading="All destinations" className="sr-only">
                {navigationSections.flatMap((section) =>
                  section.items.map((item) => (
                    <Command.Item
                      key={`all-${item.href}-${item.label}`}
                      value={item.label}
                      onSelect={() => go(item.href)}
                    >
                      {item.label}
                    </Command.Item>
                  )),
                )}
              </Command.Group>
            </Command.List>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
