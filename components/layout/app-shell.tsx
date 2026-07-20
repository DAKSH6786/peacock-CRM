"use client";

import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { CommandPalette } from "@/components/layout/command-palette";
import { HelpModal } from "@/components/layout/help-modal";
import { MobileDrawer } from "@/components/layout/mobile-drawer";
import { ShellProvider } from "@/components/layout/shell-context";

type AppShellProps = {
  role: string | null;
  userName?: string | null;
  userEmail?: string | null;
  children: React.ReactNode;
};

export function AppShell({
  role,
  userName,
  userEmail,
  children,
}: AppShellProps) {
  return (
    <ShellProvider>
      <div className="flex min-h-screen">
        <AppSidebar role={role} />
        <MobileDrawer role={role} />
        <div className="flex min-w-0 flex-1 flex-col">
          <AppHeader role={role} userName={userName} userEmail={userEmail} />
          <main className="flex-1 px-4 py-6 lg:px-8">
            <Breadcrumbs />
            {children}
          </main>
        </div>
      </div>
      <CommandPalette role={role} />
      <HelpModal />
    </ShellProvider>
  );
}
