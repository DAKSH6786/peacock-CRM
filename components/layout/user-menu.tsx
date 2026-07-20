"use client";

import { signOut } from "next-auth/react";
import { useTheme } from "next-themes";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Moon, Sun, LogOut, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { initials } from "@/lib/utils";

type UserMenuProps = {
  userName?: string | null;
  userEmail?: string | null;
};

export function UserMenu({ userName, userEmail }: UserMenuProps) {
  const { theme, setTheme } = useTheme();

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          variant="secondary"
          size="sm"
          className="gap-2 pl-1.5"
          aria-label="Open user profile menu"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--primary)] text-xs font-bold text-[var(--primary-foreground)]">
            {initials(userName)}
          </span>
          <span className="hidden max-w-[9rem] truncate md:inline">
            {userName ?? "User"}
          </span>
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 w-64 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[var(--shadow-soft)]"
        >
          <div className="px-2 py-2">
            <p className="flex items-center gap-2 text-sm font-semibold">
              <UserRound className="h-4 w-4 text-[var(--muted)]" />
              {userName ?? "User"}
            </p>
            <p className="mt-1 truncate text-xs text-[var(--muted)]">
              {userEmail}
            </p>
          </div>
          <DropdownMenu.Separator className="my-1 h-px bg-[var(--border)]" />
          <DropdownMenu.Item
            className="flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-sm outline-none hover:bg-[var(--surface-hover)] focus:bg-[var(--surface-hover)]"
            onSelect={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
            Switch to {theme === "light" ? "dark" : "light"} mode
          </DropdownMenu.Item>
          <DropdownMenu.Item
            className="flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-sm text-[var(--danger)] outline-none hover:bg-[var(--surface-hover)] focus:bg-[var(--surface-hover)]"
            onSelect={() => signOut({ callbackUrl: "/login" })}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
