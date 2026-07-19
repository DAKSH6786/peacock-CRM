import { SignOutButton } from "@/components/auth/sign-out-button";

type AppHeaderProps = {
  userName?: string | null;
  userEmail?: string | null;
};

export function AppHeader({ userName, userEmail }: AppHeaderProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-6">
      <p className="text-sm text-[var(--muted)]">Internal business OS</p>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm font-medium text-[var(--foreground)]">
            {userName ?? "User"}
          </p>
          <p className="text-xs text-[var(--muted)]">{userEmail}</p>
        </div>
        <SignOutButton />
      </div>
    </header>
  );
}
