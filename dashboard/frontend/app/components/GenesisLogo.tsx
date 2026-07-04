import Link from "next/link";

type Props = {
  href?: string;
  size?: "sm" | "md";
};

export function GenesisLogo({ href = "/site", size = "md" }: Props) {
  const box = size === "sm" ? "h-8 w-8 text-xs" : "h-10 w-10 text-sm";
  const inner = (
    <>
      <div
        className={`flex ${box} shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-genesis-accent to-indigo-600 font-bold text-white shadow-glow`}
        aria-hidden
      >
        G
      </div>
      <div>
        <p className="font-semibold tracking-tight">Genesis</p>
        <p className="text-[11px] text-genesis-muted">Цифровая компания</p>
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
