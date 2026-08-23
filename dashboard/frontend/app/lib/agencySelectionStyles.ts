/** Shared selected-state chrome for /site and /order agency surfaces. */

export function agencyCardSurface(selected: boolean, featured = false): string {
  if (selected) {
    return "border-violet-500/70 bg-gradient-to-b from-violet-950/55 to-[#0c0a12] shadow-[0_0_0_1px_rgba(139,92,246,0.35),0_0_48px_-12px_rgba(124,58,237,0.55)]";
  }
  if (featured) {
    return "border-violet-500/40 bg-gradient-to-b from-violet-950/35 to-[#0c0a12] shadow-[0_0_0_1px_rgba(139,92,246,0.12),0_20px_60px_-24px_rgba(124,58,237,0.45)]";
  }
  return "border-white/10 bg-white/[0.03]";
}

export function agencyPackageRow(selected: boolean): string {
  return selected
    ? "border-violet-500/65 bg-violet-950/40 shadow-[0_0_32px_-14px_rgba(124,58,237,0.55)]"
    : "border-white/12 bg-black/30 hover:border-violet-400/35 hover:bg-white/[0.04]";
}

export function agencyTierPill(selected: boolean): string {
  return selected
    ? "border-violet-400/60 bg-violet-600/25 text-violet-50 shadow-[0_0_24px_-8px_rgba(124,58,237,0.7)]"
    : "border-white/15 bg-black/25 text-zinc-300 hover:border-violet-400/40 hover:text-white";
}
