import { PIPELINE_STAGES } from "@/modules/intelligence";
import { cn } from "@/lib/utils";

type PipelineRailProps = {
  active?: string | null;
  completed?: string[];
  blocked?: boolean;
};

export function PipelineRail({
  active,
  completed = [],
  blocked,
}: PipelineRailProps) {
  return (
    <ol className="flex flex-wrap gap-2">
      {PIPELINE_STAGES.map((stage, index) => {
        const isDone = completed.includes(stage);
        const isActive = active === stage;
        return (
          <li
            key={stage}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold tracking-wide uppercase",
              isDone &&
                "border-[var(--primary)]/40 bg-[var(--accent-soft)] text-[var(--accent-teal)]",
              isActive &&
                !isDone &&
                "border-[var(--accent-blue)]/50 bg-[var(--surface-hover)] text-[var(--accent-blue)]",
              !isDone &&
                !isActive &&
                "border-[var(--border)] bg-[var(--surface-muted)] text-[var(--muted)]",
              blocked &&
                stage === "VERIFY" &&
                "border-[var(--danger)]/50 text-[var(--danger)]",
            )}
          >
            <span className="opacity-60">{index + 1}</span>
            <span>{stage}</span>
          </li>
        );
      })}
    </ol>
  );
}
