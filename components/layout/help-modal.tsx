"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useShell } from "@/components/layout/shell-context";

const SHORTCUTS = [
  { keys: "⌘ / Ctrl + K", action: "Open command palette" },
  { keys: "⌘ / Ctrl + /", action: "Open keyboard shortcuts" },
  { keys: "?", action: "Open help" },
  { keys: "Esc", action: "Close dialogs and menus" },
];

export function HelpModal() {
  const { helpOpen, setHelpOpen } = useShell();

  return (
    <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
      <DialogContent aria-describedby="help-desc">
        <DialogHeader>
          <DialogTitle>Help & keyboard shortcuts</DialogTitle>
          <DialogDescription id="help-desc">
            Navigate Peacock One faster with these shortcuts. Motion is reduced
            automatically when your system requests it.
          </DialogDescription>
        </DialogHeader>
        <ul className="space-y-2">
          {SHORTCUTS.map((item) => (
            <li
              key={item.keys}
              className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] px-3 py-2"
            >
              <span className="text-sm">{item.action}</span>
              <kbd className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-xs font-semibold text-[var(--muted)]">
                {item.keys}
              </kbd>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
