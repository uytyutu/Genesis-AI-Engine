import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

type Props = {
  children: ReactNode;
  className?: string;
  glow?: boolean;
  hover?: boolean;
  padding?: "sm" | "md" | "lg";
  as?: "div" | "section" | "article";
};

const PADDING = {
  sm: "p-4",
  md: "p-5",
  lg: "p-6 sm:p-8",
};

export function Card({
  children,
  className,
  glow,
  hover = true,
  padding = "md",
  as: Tag = "div",
}: Props) {
  return (
    <Tag
      className={cn(
        "genesis-card rounded-2xl border border-white/[0.06]",
        PADDING[padding],
        glow && "border-genesis-accent/25 shadow-glow",
        hover && "transition-all duration-300 ease-out",
        className
      )}
    >
      {children}
    </Tag>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <header className="mb-4 flex items-start justify-between gap-3">
      <div>
        <h2 className="text-sm font-semibold text-genesis-text">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-genesis-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}
