import { cn } from "../../lib/cn";

export function Spinner({ size = "md", className }: { size?: "sm" | "md" | "lg"; className?: string }) {
  const dim = size === "sm" ? "h-4 w-4" : size === "lg" ? "h-8 w-8" : "h-5 w-5";
  return (
    <span
      className={cn("inline-block animate-spin rounded-full border-2 border-white/20 border-t-white", dim, className)}
      role="status"
      aria-label="Загрузка"
    />
  );
}

export function Loader({ label = "Загрузка…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center" role="status">
      <Spinner size="lg" />
      <p className="text-sm text-genesis-muted">{label}</p>
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <Loader />
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={cn("animate-pulse rounded-xl bg-white/[0.06]", className)}
      aria-hidden
    />
  );
}

export function SkeletonLines({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-2" aria-label="Загрузка">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} className={`h-10 w-full ${i === count - 1 ? "w-4/5" : ""}`} />
      ))}
    </div>
  );
}
