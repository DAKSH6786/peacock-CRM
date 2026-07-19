import { Skeleton } from "@/components/shared/skeleton";

export default function AppLoading() {
  return (
    <div className="space-y-4" role="status" aria-live="polite">
      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-4 w-96 max-w-full" />
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
      <span className="sr-only">Loading</span>
    </div>
  );
}
