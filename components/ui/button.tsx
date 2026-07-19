import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap border-2 border-black font-[family-name:var(--font-body)] text-sm font-bold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "rounded-[0.75rem] bg-black text-white shadow-[8px_8px_0_0_#000000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-[4px_4px_0_0_#000000] active:translate-x-[8px] active:translate-y-[8px] active:shadow-none",
        secondary:
          "rounded-[0.75rem] bg-white text-black shadow-[4px_4px_0_0_#000000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none",
        yellow:
          "rounded-[0.75rem] bg-[#ffe17c] text-black shadow-[8px_8px_0_0_#000000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-[4px_4px_0_0_#000000]",
        sage: "rounded-[0.75rem] bg-[#b7c6c2] text-black shadow-[4px_4px_0_0_#000000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none",
        outline:
          "rounded-[0.75rem] bg-transparent text-black shadow-[4px_4px_0_0_#000000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none",
        ghost:
          "rounded-[0.75rem] border-transparent bg-transparent text-black shadow-none hover:bg-black/5",
        danger:
          "rounded-[0.75rem] bg-[#ff5f57] text-white shadow-[4px_4px_0_0_#000000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none",
      },
      size: {
        default: "h-11 px-5 py-2",
        sm: "h-9 rounded-[0.75rem] px-3 text-xs",
        lg: "h-12 rounded-[0.75rem] px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = "button", ...props }, ref) => {
    return (
      <button
        type={type}
        className={cn(buttonVariants({ variant, size, className }))}
        style={{ transitionTimingFunction: "var(--ease-press)" }}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };
