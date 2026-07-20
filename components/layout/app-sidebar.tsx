"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { filterNavByRole } from "@/components/layout/nav-config";
import { useShell } from "@/components/layout/shell-context";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { hasPermission } from "@/permissions/types";

type AppSidebarProps = {
  role: string | null;
};

export function AppSidebar({ role }: AppSidebarProps) {
  const pathname = usePathname();
  const { sidebarCollapsed, setSidebarCollapsed, setMobileNavOpen } =
    useShell();
  const sections = filterNavByRole(role, hasPermission);

  return (
    <aside
      className={cn(
        "sticky top-0 z-30 hidden h-screen shrink-0 flex-col border-r border-[var(--border)] bg-[var(--sidebar)] transition-[width] duration-200 lg:flex",
        sidebarCollapsed ? "w-[88px]" : "w-[280px]",
      )}
      aria-label="Primary"
    >
      <div className="flex h-16 items-center justify-between gap-2 border-b border-[var(--border)] px-4">
        <Logo collapsed={sidebarCollapsed} />
        <Button
          variant="ghost"
          size="icon"
          className="text-[var(--sidebar-foreground)]"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <nav className="flex-1 scrollbar-thin overflow-y-auto px-3 py-4">
        <ul className="space-y-5">
          {sections.map((section) => (
            <li key={section.id}>
              {!sidebarCollapsed ? (
                <p className="mb-2 px-2 text-[11px] font-semibold tracking-[0.14em] text-[var(--muted)] uppercase">
                  {section.label}
                </p>
              ) : (
                <span className="sr-only">{section.label}</span>
              )}
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const active =
                    pathname === item.href ||
                    (item.href !== "/dashboard" &&
                      pathname.startsWith(`${item.href}/`)) ||
                    pathname === item.href;
                  return (
                    <li key={`${section.id}-${item.href}-${item.label}`}>
                      <Link
                        href={item.href}
                        onClick={() => setMobileNavOpen(false)}
                        title={item.label}
                        className={cn(
                          "flex items-center rounded-xl px-3 py-2 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none",
                          active
                            ? "bg-[var(--sidebar-active)] text-[var(--accent-turquoise)]"
                            : "text-[var(--sidebar-foreground)] hover:bg-white/5",
                          sidebarCollapsed && "justify-center px-0",
                        )}
                        aria-current={active ? "page" : undefined}
                      >
                        {sidebarCollapsed ? (
                          <span className="text-xs font-bold">
                            {item.label.slice(0, 2)}
                          </span>
                        ) : (
                          item.label
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
