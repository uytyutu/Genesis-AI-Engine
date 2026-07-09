"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { enterFadeUp, springs } from "../../lib/motion";

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

const MOTION_TAG = {
  div: motion.div,
  section: motion.section,
  article: motion.article,
} as const;

export function Card({
  children,
  className,
  glow,
  hover = true,
  padding = "md",
  as = "div",
}: Props) {
  const reduce = useReducedMotion();
  const MotionTag = MOTION_TAG[as];

  return (
    <MotionTag
      initial={reduce ? false : enterFadeUp.initial}
      animate={enterFadeUp.animate}
      transition={springs.gentle}
      whileHover={
        hover && !reduce
          ? {
              y: -2,
              boxShadow:
                "0 1px 0 rgba(255,255,255,0.07) inset, 0 16px 44px -12px rgba(0,0,0,0.75), 0 0 28px -8px rgba(91, 141, 239, 0.14)",
              borderColor: "rgba(91, 141, 239, 0.18)",
            }
          : undefined
      }
      className={cn(
        "genesis-card rounded-2xl border border-white/[0.06]",
        PADDING[padding],
        glow && "border-genesis-accent/25 shadow-glow",
        className
      )}
    >
      {children}
    </MotionTag>
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
