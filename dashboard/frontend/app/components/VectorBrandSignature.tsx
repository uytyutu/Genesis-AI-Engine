import { ASSISTANT_NAME, ASSISTANT_TAGLINE, BRAND_SIGNATURE } from "../lib/publicBrand";

type Props = {
  /** Compact = header badge; full = welcome / about blocks */
  variant?: "compact" | "full" | "premium";
  className?: string;
  align?: "left" | "center";
};

/** Vector · by Virtus Core — consistent public product signature. */
export function VectorBrandSignature({
  variant = "compact",
  className = "",
  align = "left",
}: Props) {
  const alignClass = align === "center" ? "items-center text-center" : "items-start text-left";

  if (variant === "compact") {
    return (
      <span className={`inline-flex flex-col leading-tight ${alignClass} ${className}`}>
        <span className="text-[11px] font-bold tracking-[0.2em] text-genesis-accent uppercase">
          {ASSISTANT_NAME}
        </span>
        <span className="text-[9px] font-medium tracking-[0.18em] text-genesis-muted uppercase">
          {BRAND_SIGNATURE}
        </span>
      </span>
    );
  }

  if (variant === "premium") {
    return (
      <div className={`flex flex-col gap-0.5 ${alignClass} ${className}`}>
        <span className="text-lg font-semibold tracking-tight text-white sm:text-xl">
          {ASSISTANT_NAME}
        </span>
        <span className="text-[11px] font-medium tracking-wide text-genesis-muted">
          {ASSISTANT_TAGLINE}
        </span>
        <span className="text-[10px] font-semibold tracking-[0.22em] text-genesis-accent uppercase">
          {BRAND_SIGNATURE}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-0.5 ${alignClass} ${className}`}>
      <span className="text-base font-semibold tracking-tight text-white">{ASSISTANT_NAME}</span>
      <span className="text-[10px] font-semibold tracking-[0.2em] text-genesis-accent uppercase">
        {BRAND_SIGNATURE}
      </span>
    </div>
  );
}
