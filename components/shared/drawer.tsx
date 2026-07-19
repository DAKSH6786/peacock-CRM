"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

type DrawerProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  side?: "right" | "left";
};

export function Drawer({
  open,
  onOpenChange,
  title,
  description,
  children,
  side = "right",
}: DrawerProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50" />
        <Dialog.Content
          className={cn(
            "fixed inset-y-0 z-50 flex w-[min(96vw,28rem)] flex-col border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-soft)] focus:outline-none",
            side === "right" ? "right-0 border-l" : "left-0 border-r",
          )}
        >
          <div className="flex items-start justify-between border-b border-[var(--border)] px-5 py-4">
            <div>
              <Dialog.Title className="font-[family-name:var(--font-display)] text-lg font-semibold">
                {title}
              </Dialog.Title>
              {description ? (
                <Dialog.Description className="mt-1 text-sm text-[var(--muted)]">
                  {description}
                </Dialog.Description>
              ) : (
                <Dialog.Description className="sr-only">
                  {title}
                </Dialog.Description>
              )}
            </div>
            <Dialog.Close
              className="rounded-lg p-1 text-[var(--muted)] hover:bg-[var(--surface-hover)]"
              aria-label="Close drawer"
            >
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>
          <div className="flex-1 scrollbar-thin overflow-y-auto p-5">
            {children}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
