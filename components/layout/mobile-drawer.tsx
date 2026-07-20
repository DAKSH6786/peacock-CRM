"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";

import { Logo } from "@/components/brand/logo";
import { filterNavByRole } from "@/components/layout/nav-config";
import { useShell } from "@/components/layout/shell-context";
import { cn } from "@/lib/utils";
import { hasPermission } from "@/permissions/types";

export function MobileDrawer({ role }: { role: string | null }) {
  const pathname = usePathname();
  const { mobileNavOpen, setMobileNavOpen } = useShell();
  const sections = filterNavByRole(role, hasPermission);

  return (
    <Dialog.Root open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 lg:hidden" />
        <Dialog.Content
          className="fixed inset-y-0 left-0 z-50 w-[min(88vw,20rem)] border-r border-[var(--border)] bg-[var(--sidebar)] p-4 lg:hidden"
          aria-label="Mobile navigation"
        >
          <div className="mb-4 flex items-center justify-between">
            <Logo />
            <Dialog.Close className="rounded-lg px-2 py-1 text-sm text-[var(--sidebar-foreground)] hover:bg-white/5">
              Close
            </Dialog.Close>
          </div>
          <nav className="h-[calc(100vh-5rem)] scrollbar-thin overflow-y-auto">
            {sections.map((section) => (
              <div key={section.id} className="mb-4">
                <p className="mb-2 px-2 text-[11px] font-semibold tracking-[0.14em] text-[var(--muted)] uppercase">
                  {section.label}
                </p>
                <ul className="space-y-1">
                  {section.items.map((item) => {
                    const active =
                      pathname === item.href ||
                      pathname.startsWith(`${item.href}/`);
                    return (
                      <li key={`${section.id}-${item.href}-${item.label}`}>
                        <Link
                          href={item.href}
                          onClick={() => setMobileNavOpen(false)}
                          className={cn(
                            "block rounded-xl px-3 py-2 text-sm font-medium",
                            active
                              ? "bg-[var(--sidebar-active)] text-[var(--accent-turquoise)]"
                              : "text-[var(--sidebar-foreground)] hover:bg-white/5",
                          )}
                        >
                          {item.label}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
