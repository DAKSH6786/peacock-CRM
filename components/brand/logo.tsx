import Link from "next/link";
import { Zap } from "lucide-react";

import { cn } from "@/lib/utils";

type LogoProps = {
  href?: string;
  className?: string;
  showWordmark?: boolean;
  inverted?: boolean;
};

export function Logo({
  href = "/dashboard",
  className,
  showWordmark = true,
  inverted = false,
}: LogoProps) {
  const content = (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <span
        className="flex h-10 w-10 items-center justify-center border-2 border-black bg-black"
        aria-hidden
      >
        <Zap className="h-5 w-5 fill-[#ffe17c] text-[#ffe17c]" />
      </span>
      {showWordmark ? (
        <span
          className={cn(
            "font-[family-name:var(--font-display)] text-2xl font-extrabold tracking-tighter",
            inverted ? "text-white" : "text-black",
          )}
        >
          Peacock One
        </span>
      ) : null}
    </span>
  );

  if (!href) {
    return content;
  }

  return (
    <Link href={href} className="focus-visible:outline-none">
      {content}
    </Link>
  );
}
