/** Soft purple atmosphere tokens for Moments / Drop / sections — ANON signature. */

export type ThemeId =
  | "dream"
  | "secret"
  | "night"
  | "fire"
  | "ocean"
  | "sunset"
  | "chrome"
  | "mystery"
  | "party"
  | "candy";

export const THEME_TOKENS: Record<
  ThemeId,
  {
    labelKey: string;
    gradient: string;
    accent: string;
    glow: string;
  }
> = {
  dream: {
    labelKey: "theme.dream",
    gradient: "from-[#2a1f45]/85 via-[#3d2a5c]/45 to-[#120e1c]",
    accent: "#c9b4f0",
    glow: "rgba(201,180,240,0.32)",
  },
  secret: {
    labelKey: "theme.secret",
    gradient: "from-[#1a1228] via-[#2d1b4a]/80 to-[#0e0a16]",
    accent: "#b39ddb",
    glow: "rgba(179,157,219,0.3)",
  },
  night: {
    labelKey: "theme.night",
    gradient: "from-[#14102a] via-[#25204a]/70 to-[#0c0a18]",
    accent: "#a8b4e8",
    glow: "rgba(168,180,232,0.28)",
  },
  fire: {
    labelKey: "theme.fire",
    gradient: "from-[#2e1a2e]/90 via-[#4a2848]/50 to-[#120e1a]",
    accent: "#e8a8c8",
    glow: "rgba(232,168,200,0.3)",
  },
  ocean: {
    labelKey: "theme.ocean",
    gradient: "from-[#1a2038]/80 via-[#2a2850]/45 to-[#0e101c]",
    accent: "#b0b8e8",
    glow: "rgba(176,184,232,0.28)",
  },
  sunset: {
    labelKey: "theme.sunset",
    gradient: "from-[#32203a]/70 via-[#4a3050]/40 to-[#141018]",
    accent: "#e0b8d0",
    glow: "rgba(224,184,208,0.28)",
  },
  chrome: {
    labelKey: "theme.chrome",
    gradient: "from-[#2a2638]/85 via-[#3a3450]/40 to-[#121018]",
    accent: "#d4cce8",
    glow: "rgba(212,204,232,0.22)",
  },
  mystery: {
    labelKey: "theme.mystery",
    gradient: "from-[#100c1c] via-[#241838]/75 to-[#0a0814]",
    accent: "#9b87c9",
    glow: "rgba(155,135,201,0.3)",
  },
  party: {
    labelKey: "theme.party",
    gradient: "from-[#34204a]/60 via-[#4a3060]/35 to-[#161022]",
    accent: "#d8a8e0",
    glow: "rgba(216,168,224,0.3)",
  },
  candy: {
    labelKey: "theme.candy",
    gradient: "from-[#3a2448]/50 via-[#503060]/35 to-[#1a1224]",
    accent: "#e8c4e0",
    glow: "rgba(232,196,224,0.28)",
  },
};

export function moodToTheme(mood: string): ThemeId {
  const map: Record<string, ThemeId> = {
    sweet: "candy",
    funny: "party",
    suspicious: "mystery",
    savage: "fire",
    secret: "secret",
    beautiful: "dream",
    unexpected: "night",
  };
  return map[mood] || "dream";
}
