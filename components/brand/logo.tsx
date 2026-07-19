import Link from "next/link";

import { cn } from "@/lib/utils";

type LogoProps = {
  href?: string;
  className?: string;
  collapsed?: boolean;
};

export function Logo({
  href = "/dashboard",
  className,
  collapsed = false,
}: LogoProps) {
  const content = (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <span
        className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl shadow-[var(--shadow-glow)]"
        style={{
          background: "linear-gradient(135deg, #0f766e, #0284c7 55%, #7c3aed)",
        }}
        aria-hidden
      >
        <span className="absolute inset-[3px] rounded-[0.65rem] bg-[#0a101c]" />
        <span
          className="relative h-3 w-3 rounded-full bg-[var(--accent-turquoise)]"
          style={{ boxShadow: "0 0 12px rgba(45, 212, 191, 0.8)" }}
        />
      </span>
      {!collapsed ? (
        <span className="min-w-0">
          <span className="block font-[family-name:var(--font-display)] text-base font-bold tracking-tight text-[var(--sidebar-foreground)]">
            Peacock One
          </span>
          <span className="block truncate text-[11px] font-medium text-[var(--muted)]">
            Digital Peacock OS
          </span>
        </span>
      ) : null}
    </span>
  );

  if (!href) return content;
  return (
    <Link href={href} className="rounded-xl focus-visible:outline-none">
      {content}
    </Link>
  );
}
