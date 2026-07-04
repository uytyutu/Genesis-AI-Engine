export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-white/5 ${className}`}
      aria-hidden
    />
  );
}

export function PackageSkeleton() {
  return (
    <div className="space-y-2" aria-label="Загрузка пакетов">
      {[1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-11 w-full" />
      ))}
    </div>
  );
}
