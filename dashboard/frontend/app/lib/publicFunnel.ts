/**
 * M3.3 — Public funnel: every screen leads to the next step naturally.
 */

export type PublicFunnelStep = {
  id: string;
  label: string;
  href: string;
  description: string;
};

export const PUBLIC_FUNNEL: PublicFunnelStep[] = [
  {
    id: "home",
    label: "Vector",
    href: "/site",
    description: "Расскажите о бизнесе — черновик появится справа",
  },
];

export const M3_3_GATE = [
  "Может ли человек понять продукт, не устанавливая его?",
  "Возникло ли желание установить приложение?",
  "Понятно ли, зачем существуют Public и Client?",
  "Не создаётся ли ощущение, что Public — сломанная версия приложения?",
] as const;

/** Public vs Client decision gate for new features. */
export function belongsOnPublicSurface(capability: "intro" | "lite_chat" | "demo" | "full_project" | "memory" | "commerce"): boolean {
  return capability === "intro" || capability === "lite_chat" || capability === "demo";
}

export function nextFunnelStep(currentPath: string): PublicFunnelStep | null {
  const idx = PUBLIC_FUNNEL.findIndex((s) => {
    if (s.id === "home") return currentPath.startsWith("/site");
    return currentPath === s.href || currentPath.startsWith(`${s.href}/`);
  });
  if (idx < 0 || idx >= PUBLIC_FUNNEL.length - 1) return null;
  return PUBLIC_FUNNEL[idx + 1];
}
