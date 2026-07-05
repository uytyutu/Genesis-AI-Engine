import { Skeleton } from "./ui/Loader";

/** Dashboard loading skeleton — Genesis UI kit */
export function DashboardSkeleton() {
  return (
    <div className="space-y-5 animate-fade-up" aria-label="Загрузка пульта">
      <Skeleton className="h-24 w-full rounded-2xl" />
      <div className="grid gap-5 lg:grid-cols-5">
        <div className="space-y-5 lg:col-span-3">
          <Skeleton className="h-40 w-full rounded-2xl" />
          <Skeleton className="h-32 w-full rounded-2xl" />
          <Skeleton className="h-48 w-full rounded-2xl" />
        </div>
        <div className="space-y-5 lg:col-span-2">
          <Skeleton className="h-56 w-full rounded-2xl" />
          <Skeleton className="h-40 w-full rounded-2xl" />
        </div>
      </div>
    </div>
  );
}
