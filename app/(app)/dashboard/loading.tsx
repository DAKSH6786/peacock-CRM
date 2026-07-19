import { Skeleton } from "@/components/shared/skeleton";

export default function DashboardLoading() {
  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <Skeleton className="h-10 w-72" />
      <Skeleton className="h-4 w-full max-w-xl" />
      <Skeleton className="h-28 w-full" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Skeleton className="h-72" />
        <Skeleton className="h-72" />
      </div>
      <span className="sr-only">Loading dashboard</span>
    </div>
  );
}
