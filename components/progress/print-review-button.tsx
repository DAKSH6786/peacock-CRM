"use client";

import { Button } from "@/components/ui/button";

export function PrintReviewButton() {
  return (
    <Button
      type="button"
      className="print:hidden"
      onClick={() => window.print()}
    >
      Print / Save as PDF
    </Button>
  );
}
