import { cn } from "../../lib/cn";

type Variant = "default" | "accent" | "success" | "warning" | "muted" | "outline";

const STYLES: Record<Variant, string> = {
  default: "bg-genesis-elevated/80 text-genesis-text border-genesis-border-subtle",
  accent: "bg-genesis-accent/15 text-genesis-accent border-genesis-accent/30",
  success: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  warning: "bg-amber-500/15 text-amber-200 border-amber-500/30",
  muted: "bg-white/5 text-genesis-muted border-transparent",
  outline: "bg-transparent text-genesis-muted border-genesis-border-subtle",
};

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        STYLES[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
