"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { primaryNav } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";
import { hasPermission, type Permission } from "@/permissions/types";

type AppSidebarProps = {
  role: string | null;
};

export function AppSidebar({ role }: AppSidebarProps) {
  const pathname = usePathname();

  const visible = primaryNav.filter((item) => {
    if (!item.permission) return true;
    return hasPermission(
      role as Parameters<typeof hasPermission>[0],
      item.permission as Permission,
    );
  });

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--sidebar)]">
      <div className="border-b border-[var(--border)] px-5 py-6">
        <Link href="/dashboard" className="block focus-visible:outline-none">
          <p className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-[var(--brand)]">
            Peacock One
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Digital Peacock operating system
          </p>
        </Link>
      </div>
      <nav aria-label="Primary" className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {visible.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "block rounded-md px-3 py-2 text-sm transition-colors focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none",
                    active
                      ? "bg-[var(--brand-soft)] font-medium text-[var(--brand)]"
                      : "text-[var(--foreground)] hover:bg-[var(--surface-muted)]",
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
