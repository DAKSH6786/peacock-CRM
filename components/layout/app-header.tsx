"use client";

import { HelpCircle, Menu, Search } from "lucide-react";

import { ApprovalInbox } from "@/components/layout/approval-inbox";
import { NotificationCenter } from "@/components/layout/notification-center";
import { OrganizationSwitcher } from "@/components/layout/org-switcher";
import { QuickCreateMenu } from "@/components/layout/quick-create";
import { useShell } from "@/components/layout/shell-context";
import { UserMenu } from "@/components/layout/user-menu";
import { Button } from "@/components/ui/button";

type AppHeaderProps = {
  userName?: string | null;
  userEmail?: string | null;
  role: string | null;
};

export function AppHeader({ userName, userEmail, role }: AppHeaderProps) {
  const { setMobileNavOpen, setCommandOpen, setHelpOpen } = useShell();

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-[var(--topbar)] backdrop-blur-md">
      <div className="flex h-16 items-center gap-3 px-4 lg:px-6">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          aria-label="Open navigation menu"
          onClick={() => setMobileNavOpen(true)}
        >
          <Menu className="h-4 w-4" />
        </Button>

        <OrganizationSwitcher />

        <button
          type="button"
          onClick={() => setCommandOpen(true)}
          className="ml-auto flex h-10 min-w-0 flex-1 items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 text-left text-sm text-[var(--muted)] transition-colors hover:border-[var(--border-strong)] hover:text-[var(--foreground)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:outline-none md:max-w-md lg:ml-6"
          aria-label="Open global search"
        >
          <Search className="h-4 w-4 shrink-0" />
          <span className="truncate">Search Peacock One…</span>
          <kbd className="ml-auto hidden rounded-md border border-[var(--border)] px-1.5 py-0.5 text-[10px] font-semibold sm:inline">
            ⌘K
          </kbd>
        </button>

        <div className="flex items-center gap-1 sm:gap-2">
          <QuickCreateMenu role={role} />
          <ApprovalInbox />
          <NotificationCenter />
          <Button
            variant="ghost"
            size="icon"
            aria-label="Open help and shortcuts"
            onClick={() => setHelpOpen(true)}
          >
            <HelpCircle className="h-4 w-4" />
          </Button>
          <UserMenu userName={userName} userEmail={userEmail} />
        </div>
      </div>
    </header>
  );
}
