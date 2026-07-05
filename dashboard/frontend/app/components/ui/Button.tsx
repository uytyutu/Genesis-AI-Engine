"use client";

import Link from "next/link";
import type { ComponentProps, ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";
import type { ButtonSize, ButtonVariant } from "../../lib/tokens";
import { Spinner } from "./Loader";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  children: ReactNode;
};

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-genesis-accent to-indigo-600 text-white shadow-glow hover:brightness-110 border-transparent",
  secondary:
    "border border-genesis-border bg-genesis-elevated/80 text-genesis-text hover:border-genesis-accent/40 hover:bg-genesis-panel",
  ghost:
    "border border-transparent text-genesis-muted hover:bg-genesis-elevated hover:text-white",
  success:
    "bg-gradient-to-r from-genesis-accent to-indigo-600 text-white shadow-glow hover:brightness-110 border-transparent",
  danger:
    "border border-rose-500/40 bg-rose-950/40 text-rose-100 hover:bg-rose-950/60",
};

const SIZE: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs rounded-lg",
  md: "px-4 py-2.5 text-sm rounded-xl",
  lg: "px-6 py-3.5 text-sm rounded-xl",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  fullWidth = false,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: Props) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200 ease-out",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/70 focus-visible:ring-offset-2 focus-visible:ring-offset-genesis-bg",
        VARIANT[variant],
        SIZE[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
}

export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  fullWidth,
  className,
  children,
  ...props
}: {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  className?: string;
  children: ReactNode;
} & Omit<ComponentProps<typeof Link>, "href" | "className" | "children">) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-semibold transition-all duration-200 ease-out",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/70 focus-visible:ring-offset-2 focus-visible:ring-offset-genesis-bg",
        VARIANT[variant],
        SIZE[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {children}
    </Link>
  );
}
