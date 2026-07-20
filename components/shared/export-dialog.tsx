"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

type ExportDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onExport: (format: "csv" | "xlsx") => void;
  disabled?: boolean;
};

export function ExportDialog({
  open,
  onOpenChange,
  onExport,
  disabled,
}: ExportDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export records</DialogTitle>
          <DialogDescription>
            Exports respect your role permissions and current table filters.
          </DialogDescription>
        </DialogHeader>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant="secondary"
            disabled={disabled}
            onClick={() => onExport("csv")}
          >
            Export CSV
          </Button>
          <Button
            variant="secondary"
            disabled={disabled}
            onClick={() => onExport("xlsx")}
          >
            Export Excel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
