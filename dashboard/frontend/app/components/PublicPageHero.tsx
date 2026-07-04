import type { ReactNode } from "react";
import { Badge } from "./ui/Badge";
import { cn } from "../lib/cn";

type Props = {
  badge?: string;
  badgeVariant?: "accent" | "success" | "warning" | "muted";
  title: ReactNode;
  description?: string;
  children?: ReactNode;
  className?: string;
  centered?: boolean;
};

export function PublicPageHero({
  badge,
  badgeVariant = "accent",
  title,
  description,
  children,
  className,
  centered = true,
}: Props) {
  return (
    <section
      className={cn(
        "py-10 sm:py-14 animate-fade-up",
        centered && "text-center",
        className
      )}
    >
      {badge && (
        <Badge variant={badgeVariant} className="tracking-[0.2em]">
          {badge}
        </Badge>
      )}
      <h1 className={cn("text-3xl font-bold sm:text-4xl", badge ? "mt-3" : "")}>{title}</h1>
      {description && (
        <p className="mx-auto mt-4 max-w-2xl text-sm text-genesis-muted sm:text-base">
          {description}
        </p>
      )}
      {children && <div className="mt-8">{children}</div>}
    </section>
  );
}
