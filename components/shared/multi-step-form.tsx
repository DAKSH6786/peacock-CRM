"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Step = {
  id: string;
  title: string;
  description?: string;
};

type MultiStepFormProps = {
  steps: Step[];
  currentStep: number;
  onBack?: () => void;
  onNext?: () => void;
  onSubmit?: () => void;
  children: React.ReactNode;
  isLast?: boolean;
};

export function MultiStepForm({
  steps,
  currentStep,
  onBack,
  onNext,
  onSubmit,
  children,
  isLast,
}: MultiStepFormProps) {
  return (
    <div className="peacock-card p-5">
      <ol className="mb-6 flex flex-wrap gap-2" aria-label="Form steps">
        {steps.map((step, index) => {
          const active = index === currentStep;
          const complete = index < currentStep;
          return (
            <li
              key={step.id}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-semibold",
                active &&
                  "border-[var(--accent-teal)] bg-[var(--accent-soft)] text-[var(--accent-teal)]",
                complete && "border-[var(--border)] text-[var(--foreground)]",
                !active &&
                  !complete &&
                  "border-[var(--border)] text-[var(--muted)]",
              )}
              aria-current={active ? "step" : undefined}
            >
              {index + 1}. {step.title}
            </li>
          );
        })}
      </ol>
      <div className="mb-6">{children}</div>
      <div className="flex justify-between gap-2">
        <Button variant="outline" onClick={onBack} disabled={currentStep === 0}>
          Back
        </Button>
        {isLast ? (
          <Button onClick={onSubmit}>Submit</Button>
        ) : (
          <Button onClick={onNext}>Continue</Button>
        )}
      </div>
    </div>
  );
}
