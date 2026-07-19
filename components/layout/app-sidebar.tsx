"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/brand/logo";
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
    <aside className="flex w-72 shrink-0 flex-col border-r-2 border-black bg-[#171e19] text-white">
      <div className="border-b-2 border-black bg-[#ffe17c] px-5 py-5">
        <Logo />
        <p className="mt-2 font-[family-name:var(--font-body)] text-xs font-bold text-black/70">
          Digital Peacock OS
        </p>
      </div>
      <nav aria-label="Primary" className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-2">
          {visible.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "block rounded-[0.75rem] border-2 px-3 py-2 font-[family-name:var(--font-body)] text-sm font-bold transition-all duration-200 focus-visible:ring-2 focus-visible:ring-[#ffe17c] focus-visible:outline-none",
                    active
                      ? "border-black bg-[#ffe17c] text-black shadow-[4px_4px_0_0_#000000]"
                      : "border-transparent text-[#b7c6c2] hover:border-black hover:bg-[#272727] hover:text-white",
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
      <div className="border-t-2 border-black p-4">
        <div className="rounded-[0.75rem] border-2 border-black bg-[#272727] p-3">
          <p className="font-[family-name:var(--font-display)] text-sm font-extrabold tracking-tighter text-[#ffe17c]">
            Neo-Brutal Ops
          </p>
          <p className="mt-1 text-xs font-medium text-[#b7c6c2]">
            High contrast. Zero blur. Full clarity.
          </p>
        </div>
      </div>
    </aside>
  );
}
