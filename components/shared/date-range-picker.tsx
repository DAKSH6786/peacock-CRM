"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

type DateRangePickerProps = {
  from: string;
  to: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
};

export function DateRangePicker({
  from,
  to,
  onFromChange,
  onToChange,
}: DateRangePickerProps) {
  return (
    <fieldset className="grid gap-3 sm:grid-cols-2">
      <legend className="sr-only">Date range</legend>
      <div className="space-y-1.5">
        <Label htmlFor="date-from">From</Label>
        <Input
          id="date-from"
          type="date"
          value={from}
          onChange={(event) => onFromChange(event.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="date-to">To</Label>
        <Input
          id="date-to"
          type="date"
          value={to}
          onChange={(event) => onToChange(event.target.value)}
        />
      </div>
    </fieldset>
  );
}
