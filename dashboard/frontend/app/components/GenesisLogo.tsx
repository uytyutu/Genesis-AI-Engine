import Link from "next/link";
import { GenesisMark } from "./GenesisMark";

type Props = {
  href?: string;
  size?: "sm" | "md";
};

export function GenesisLogo({ href = "/site", size = "md" }: Props) {
  const markSize = size === "sm" ? "h-8 w-8" : "h-10 w-10";
  const inner = (
    <>
      <GenesisMark className={`${markSize} shrink-0 shadow-glow`} />
      <div>
        <p className="font-semibold tracking-tight text-genesis-text">Genesis</p>
        <p className="text-[11px] text-genesis-muted">Company OS</p>
      </div>
    </>
  );

  if (href) {
    return (
      <Link href={href} className="group flex items-center gap-3 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-genesis-accent/60">
        {inner}
      </Link>
    );
  }
  return <div className="flex items-center gap-3">{inner}</div>;
}
