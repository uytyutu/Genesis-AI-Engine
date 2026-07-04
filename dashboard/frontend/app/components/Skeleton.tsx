export { Skeleton, SkeletonLines } from "./ui/Loader";
import { Skeleton } from "./ui/Loader";

export function PackageSkeleton() {
  return (
    <div className="space-y-2" aria-label="Загрузка пакетов">
      {[1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-11 w-full" />
      ))}
    </div>
  );
}
