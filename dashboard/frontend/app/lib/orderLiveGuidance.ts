/**
 * Mission 3A / A1.3 — Live preview + AI guidance (client-only).
 * Mirrors Factory Composer rules without calling Factory / LLM / ZIP.
 */

import { uiLangForMarket } from "./marketLang";

export type OrderLiveInput = {
  businessName: string;
  description: string;
  niche: string;
  brandStyle: string;
  packageId: string;
  marketCode: string;
  city: string;
  email: string;
  phone: string;
  needsLogo: boolean;
  hasMaterials: boolean;
  formStep: number;
};

export type OrderLivePalette = {
  primary: string;
  primaryDark: string;
  accent: string;
  gradient: string;
  surface: string;
  ink: string;
};

export type OrderLiveGuidance = {
  nicheId: string;
  styleId: string;
  heroLayout: string;
  heroHint: string;
  marketCode: string;
  languageCode: string;
  packageId: string;
  palette: OrderLivePalette;
  previewTitle: string;
  previewTagline: string;
  /** 0–6 filled blocks for ■■□□□□ style UI */
  progressFilled: number;
  progressTotal: number;
  readyIds: string[];
  remainingIds: string[];
};

/** Niche → preferred hero layouts (Factory hero_composer allowlist, first = primary). */
const NICHE_HERO: Record<string, { layouts: string[]; hint: string }> = {
  dental: { layouts: ["A", "C", "E"], hint: "Doctor + Clinic" },
  auto: { layouts: ["B", "D", "F"], hint: "Workshop + Trust" },
  law: { layouts: ["C", "A", "E"], hint: "Authority + Clarity" },
  energy: { layouts: ["A", "D", "E"], hint: "Clean + Efficient" },
  beauty: { layouts: ["E", "A", "C"], hint: "Soft + Showcase" },
  green: { layouts: ["A", "D", "E"], hint: "Nature + Calm" },
  computer: { layouts: ["A", "B", "C"], hint: "Tech + Service" },
  appliance: { layouts: ["A", "B", "F"], hint: "Repair + Local" },
  handwerk: { layouts: ["B", "F", "A"], hint: "Craft + Direct" },
  generic: { layouts: ["A", "B", "C"], hint: "Clear + Local" },
};

/** Brand style packs — aligned with backend brand_style.py (subset). */
const STYLE_PALETTE: Record<string, OrderLivePalette> = {
  modern: {
    primary: "#2563eb",
    primaryDark: "#1e3a8a",
    accent: "#38bdf8",
    gradient: "linear-gradient(145deg,#0f172a 0%,#1e40af 55%,#0369a1 100%)",
    surface: "#f8fafc",
    ink: "#0f172a",
  },
  premium: {
    primary: "#1c1917",
    primaryDark: "#0c0a09",
    accent: "#d4af37",
    gradient: "linear-gradient(160deg,#0c0a09 0%,#292524 50%,#44403c 100%)",
    surface: "#fafaf9",
    ink: "#1c1917",
  },
  elegant: {
    primary: "#4c1d95",
    primaryDark: "#2e1065",
    accent: "#c4b5fd",
    gradient: "linear-gradient(150deg,#1e1b4b 0%,#4c1d95 60%,#6d28d9 100%)",
    surface: "#faf5ff",
    ink: "#1e1b4b",
  },
  minimal: {
    primary: "#171717",
    primaryDark: "#0a0a0a",
    accent: "#a3a3a3",
    gradient: "linear-gradient(180deg,#171717 0%,#404040 100%)",
    surface: "#fafafa",
    ink: "#171717",
  },
  corporate: {
    primary: "#0f766e",
    primaryDark: "#134e4a",
    accent: "#5eead4",
    gradient: "linear-gradient(145deg,#042f2e 0%,#0f766e 55%,#115e59 100%)",
    surface: "#f0fdfa",
    ink: "#134e4a",
  },
  friendly: {
    primary: "#ea580c",
    primaryDark: "#9a3412",
    accent: "#fdba74",
    gradient: "linear-gradient(145deg,#7c2d12 0%,#ea580c 55%,#f97316 100%)",
    surface: "#fff7ed",
    ink: "#9a3412",
  },
};

const NICHE_DEFAULT_STYLE: Record<string, string> = {
  dental: "modern",
  auto: "corporate",
  law: "elegant",
  energy: "modern",
  beauty: "elegant",
  green: "friendly",
  computer: "minimal",
  appliance: "friendly",
  handwerk: "corporate",
  generic: "modern",
};

const LANG_LABEL: Record<string, string> = {
  de: "Deutsch",
  en: "English",
  fr: "Français",
  es: "Español",
  nl: "Nederlands",
  it: "Italiano",
  pt: "Português",
  pl: "Polski",
  cs: "Čeština",
  uk: "Українська",
  ru: "Русский",
};

export function normalizeNicheId(raw: string | null | undefined): string {
  const n = (raw || "generic").trim().toLowerCase() || "generic";
  return NICHE_HERO[n] ? n : "generic";
}

export function resolveStyleId(brandStyle: string, nicheId: string): string {
  const s = (brandStyle || "auto").trim().toLowerCase();
  if (s && s !== "auto" && STYLE_PALETTE[s]) return s;
  return NICHE_DEFAULT_STYLE[nicheId] || "modern";
}

export function languageLabel(code: string): string {
  return LANG_LABEL[code] || code.toUpperCase();
}

export function buildOrderLiveGuidance(input: OrderLiveInput): OrderLiveGuidance {
  const nicheId = normalizeNicheId(input.niche);
  const hero = NICHE_HERO[nicheId] || NICHE_HERO.generic;
  const styleId = resolveStyleId(input.brandStyle, nicheId);
  const palette = STYLE_PALETTE[styleId] || STYLE_PALETTE.modern;
  const market = (input.marketCode || "DE").trim().toUpperCase() || "DE";
  const languageCode = uiLangForMarket(market);
  const packageId = (input.packageId || "basic").toLowerCase();
  const name = input.businessName.trim() || "Your business";
  const tag =
    input.description.trim().slice(0, 80) ||
    (input.city.trim() ? `${nicheId} · ${input.city.trim()}` : `${nicheId} · ${market}`);

  const readyIds: string[] = [];
  const remainingIds: string[] = [];

  const hasStructure = Boolean(input.niche && input.niche !== "generic") || input.description.trim().length >= 8;
  const hasStyle = Boolean(styleId);
  const hasColors = Boolean(palette.primary);
  const hasPackage = Boolean(packageId);
  const hasContacts = Boolean(input.email.trim() && input.email.includes("@"));
  const hasPhoneOrCity = Boolean(input.phone.trim() || input.city.trim());
  const hasBrandAssets = input.hasMaterials || !input.needsLogo || input.formStep >= 3;

  const flags: Array<[string, boolean]> = [
    ["structure", hasStructure],
    ["style", hasStyle],
    ["colors", hasColors],
    ["package", hasPackage],
    ["contacts", hasContacts],
    ["details", hasPhoneOrCity || hasBrandAssets],
  ];
  for (const [id, ok] of flags) {
    if (ok) readyIds.push(id);
    else remainingIds.push(id);
  }

  const progressTotal = 6;
  const progressFilled = Math.min(progressTotal, readyIds.length);

  return {
    nicheId,
    styleId,
    heroLayout: hero.layouts[0] || "A",
    heroHint: hero.hint,
    marketCode: market,
    languageCode,
    packageId,
    palette,
    previewTitle: name,
    previewTagline: tag,
    progressFilled,
    progressTotal,
    readyIds,
    remainingIds,
  };
}

export function progressBars(filled: number, total: number): string {
  const f = Math.max(0, Math.min(total, filled));
  return "■".repeat(f) + "□".repeat(Math.max(0, total - f));
}
