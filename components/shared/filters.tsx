"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type FilterField = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

type AdvancedFiltersProps = {
  fields: FilterField[];
  onClear: () => void;
  savedViews?: Array<{ id: string; name: string; onSelect: () => void }>;
};

export function AdvancedFilters({
  fields,
  onClear,
  savedViews = [],
}: AdvancedFiltersProps) {
  return (
    <section className="peacock-card mb-4 p-4" aria-label="Advanced filters">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Filters</h2>
        <Button variant="ghost" size="sm" onClick={onClear}>
          Clear
        </Button>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {fields.map((field) => (
          <div key={field.id} className="space-y-1.5">
            <Label htmlFor={field.id}>{field.label}</Label>
            <Input
              id={field.id}
              value={field.value}
              onChange={(event) => field.onChange(event.target.value)}
              placeholder={field.placeholder}
            />
          </div>
        ))}
      </div>
      {savedViews.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2" aria-label="Saved views">
          {savedViews.map((view) => (
            <Button
              key={view.id}
              variant="subtle"
              size="sm"
              onClick={view.onSelect}
            >
              {view.name}
            </Button>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export function SearchBar({
  value,
  onChange,
  placeholder = "Search…",
  label = "Search",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
}) {
  return (
    <div className="max-w-sm">
      <Label htmlFor="shared-search" className="sr-only">
        {label}
      </Label>
      <Input
        id="shared-search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}
