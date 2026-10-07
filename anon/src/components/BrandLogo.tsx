"use client";

import Link from "next/link";
import { AnonMark } from "./AnonCharacter";

type Variant = "wordmark" | "icon" | "full";

export function BrandLogo({
  variant = "wordmark",
  href = "/",
  size = 32,
  className = "",
}: {
  variant?: Variant;
  href?: string | null;
  size?: number;
  className?: string;
}) {
  const inner =
    variant === "icon" ? (
      <AnonMark size={size} />
    ) : (
      <span className={`inline-flex items-center gap-2.5 ${className}`}>
        <AnonMark size={size} />
        <span
          className="font-bold tracking-[0.2em] text-white"
          style={{ fontSize: Math.max(14, size * 0.55) }}
        >
          ANON
        </span>
      </span>
    );

  if (!href) return inner;
  return (
    <Link href={href} className={`inline-flex items-center ${className}`} aria-label="ANON">
      {inner}
    </Link>
  );
}
