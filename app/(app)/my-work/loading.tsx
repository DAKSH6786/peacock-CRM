import { Skeleton } from "@/components/shared/skeleton";

export default function MyWorkLoading() {
  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <Skeleton className="h-10 w-48" />
      <Skeleton className="h-4 w-96 max-w-full" />
      <div className="grid gap-4 xl:grid-cols-2">
        <Skeleton className="h-56" />
        <Skeleton className="h-56" />
        <Skeleton className="h-56" />
        <Skeleton className="h-56" />
      </div>
      <span className="sr-only">Loading My Work</span>
    </div>
  );
}
