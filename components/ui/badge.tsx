import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "yellow" | "sage" | "white" | "dark";
};

export function Badge({ className, variant = "white", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border-2 border-black px-3 py-1 font-[family-name:var(--font-body)] text-xs font-bold",
        variant === "white" && "bg-white text-black",
        variant === "yellow" && "bg-[#ffe17c] text-black",
        variant === "sage" && "bg-[#b7c6c2] text-black",
        variant === "dark" && "bg-[#171e19] text-white",
        variant === "default" && "bg-black text-white",
        className,
      )}
      {...props}
    />
  );
}
