import Link from "next/link";
import { VirtusMark } from "./VirtusMark";
import { ASSISTANT_NAME, BRAND_NAME, BRAND_SIGNATURE } from "../lib/publicBrand";

type Props = {
  href?: string;
  size?: "sm" | "md";
};

export function VirtusLogo({ href = "/site", size = "md" }: Props) {
  const markSize = size === "sm" ? "h-8 w-8" : "h-10 w-10";
  const inner = (
    <>
      <VirtusMark className={`${markSize} shrink-0 shadow-glow`} />
      <div>
        <p className="font-semibold tracking-tight text-genesis-text">{ASSISTANT_NAME}</p>
        <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-genesis-muted">
          {BRAND_SIGNATURE}
        </p>
      </div>
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        onClick={() => {
          if (href === "/site") window.dispatchEvent(new Event("genesis:home"));
        }}
        className="group flex items-center gap-3 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/60"
      >
        {inner}
      </Link>
    );
  }
  return <div className="flex items-center gap-3">{inner}</div>;
}

/** Mission Control / operator shell — platform name */
export function VirtusCoreLogo({ href = "/" }: { href?: string }) {
  const inner = (
    <>
      <VirtusMark className="h-10 w-10 shrink-0 shadow-glow" />
      <div className="min-w-0">
        <p className="font-semibold tracking-tight text-genesis-text">{BRAND_NAME}</p>
        <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-genesis-muted">
          {ASSISTANT_NAME} · {BRAND_SIGNATURE}
        </p>
      </div>
    </>
  );
  if (href) {
    return (
      <Link href={href} className="flex items-center gap-3">
        {inner}
      </Link>
    );
  }
  return <div className="flex items-center gap-3">{inner}</div>;
}

/** @deprecated public header uses VirtusLogo */
export const GenesisLogo = VirtusLogo;
