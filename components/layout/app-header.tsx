import { SignOutButton } from "@/components/auth/sign-out-button";
import { Badge } from "@/components/ui/badge";

type AppHeaderProps = {
  userName?: string | null;
  userEmail?: string | null;
};

export function AppHeader({ userName, userEmail }: AppHeaderProps) {
  return (
    <header className="flex h-20 items-center justify-between border-b-2 border-black bg-[#ffe17c] px-6">
      <div className="flex items-center gap-3">
        <Badge variant="white">INTERNAL</Badge>
        <p className="hidden font-[family-name:var(--font-body)] text-sm font-bold text-black sm:block">
          Business operating system
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden text-right sm:block">
          <p className="font-[family-name:var(--font-display)] text-sm font-extrabold tracking-tighter text-black">
            {userName ?? "User"}
          </p>
          <p className="text-xs font-medium text-black/70">{userEmail}</p>
        </div>
        <SignOutButton />
      </div>
    </header>
  );
}
