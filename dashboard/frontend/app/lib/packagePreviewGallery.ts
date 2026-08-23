/**
 * Package preview gallery — Path A order / storefront.
 *
 * OWNER SSOT — do NOT mix tiers:
 *
 *   Basic    = sites/basic/<niche> + stores/basic/<niche>
 *   Business = cinematic flagships (disk under /premium/) + sites/business when present
 *   Premium  = empty until product ready (do not re-label Business as Premium)
 *
 * Forbidden: sites/premium/* legacy · Family Care / psychology demos.
 */

import {
  PUBLIC_VITRINE_STORES_BASIC,
  PUBLIC_VITRINE_STORES_BUSINESS,
  PUBLIC_VITRINE_STORES_PREMIUM,
  PUBLIC_VITRINE_THUMB_VERSION,
  PUBLIC_VITRINE_WEBSITES_BASIC,
  PUBLIC_VITRINE_WEBSITES_BUSINESS,
  PUBLIC_VITRINE_WEBSITES_PREMIUM,
  isBasicStandardHref,
  isBusinessHref,
  isPremiumCinematicHref,
  type PublicVitrineDemo,
} from "./publicVitrineCatalog";

export type PackagePreviewTier = "basic" | "business" | "premium";

export type PackagePreviewSlide = {
  /**
   * Thumb URL: absolute `/vitrine/...` (vitrine SSOT) or relative under
   * `/package-previews/` (legacy tier galleries).
   */
  src: string;
  alt: string;
  niche?: string;
  /** Optional full HTML demo (opened in new tab, not iframe) */
  siteSrc?: string;
  kind: "image";
};

function vitrineDemoToSlide(demo: PublicVitrineDemo): PackagePreviewSlide {
  return {
    src: `${demo.thumb}?v=${PUBLIC_VITRINE_THUMB_VERSION}`,
    siteSrc: demo.href.replace(/^\/package-previews\//, ""),
    alt: `${demo.fallback} · ${demo.badge || ""} · ${demo.kind === "store" ? "AI Store" : "Website"}`,
    niche: demo.niche,
    kind: "image",
  };
}

function vitrinePoolFor(
  tier: PackagePreviewTier,
  kind: "website" | "store",
): PublicVitrineDemo[] {
  if (kind === "store") {
    if (tier === "premium") return PUBLIC_VITRINE_STORES_PREMIUM;
    if (tier === "business") return PUBLIC_VITRINE_STORES_BUSINESS;
    return PUBLIC_VITRINE_STORES_BASIC;
  }
  if (tier === "premium") return PUBLIC_VITRINE_WEBSITES_PREMIUM;
  if (tier === "business") return PUBLIC_VITRINE_WEBSITES_BUSINESS;
  return PUBLIC_VITRINE_WEBSITES_BASIC;
}

/** Hard gate: never return a slide whose path belongs to another package tier. */
function assertSlideMatchesTier(
  tier: PackagePreviewTier,
  slide: PackagePreviewSlide | null,
): PackagePreviewSlide | null {
  if (!slide?.siteSrc) return slide;
  const href = slide.siteSrc.startsWith("/")
    ? slide.siteSrc
    : `/package-previews/${slide.siteSrc}`;
  if (tier === "premium" && !isPremiumCinematicHref(href)) return null;
  if (tier === "basic" && !isBasicStandardHref(href)) return null;
  if (tier === "business") {
    if (isBasicStandardHref(href) || href.includes("/sites/premium/") || href.includes("/stores/premium/")) {
      return null;
    }
    if (!isBusinessHref(href)) return null;
  }
  return slide;
}

/** Map order-form niche labels (Salon, Mode, …) to catalog niche keys. */
export function normalizeOrderNicheKey(niche?: string | null): string {
  const raw = (niche || "").trim().toLowerCase();
  if (!raw) return "";
  // Removed niches — never map to a live demo
  if (
    raw.includes("family") ||
    raw.includes("familien") ||
    raw.includes("psycholog") ||
    raw === "family_psychology" ||
    raw === "family_care"
  ) {
    return "";
  }
  const aliases: Record<string, string> = {
    salon: "beauty",
    beauty: "beauty",
    nail: "beauty",
    nails: "beauty",
    brow: "beauty",
    brows: "beauty",
    barber: "barbershop",
    barbershop: "barbershop",
    zahnarzt: "dental",
    dental: "dental",
    restaurant: "restaurant",
    gastronomie: "restaurant",
    hotdog: "restaurant",
    "hot-dog": "restaurant",
    fashion: "fashion",
    mode: "fashion",
    boutique: "fashion",
    electronics: "electronics",
    elektronik: "electronics",
    handwerk: "handwerk",
    auto: "auto",
    werkstatt: "auto",
    law: "law",
    anwalt: "law",
    rechtsanwalt: "law",
    gartenpflege: "gartenpflege",
    dachreinigung: "dachreinigung",
    zaunbau: "zaunbau",
    food: "food",
    furniture: "furniture",
    accessories: "accessories",
  };
  if (aliases[raw]) return aliases[raw]!;
  for (const [key, value] of Object.entries(aliases)) {
    if (raw.includes(key)) return value;
  }
  return raw;
}

/** Flagship niche when order/pricing has no niche yet. */
function flagshipNiche(tier: PackagePreviewTier, kind: "website" | "store"): string {
  if (kind === "store") return "fashion";
  if (tier === "business") return "restaurant";
  if (tier === "basic") return "beauty";
  return "";
}

/**
 * Order checkout preview: only PUBLISHED showcase demos for that package tier.
 * Premium → null until Premium demos exist.
 */
export function resolveExactOrderPreview(
  packageId: string | null | undefined,
  niche?: string | null,
  kind: "website" | "store" = "website",
): PackagePreviewSlide | null {
  const tier = normalizePreviewTier(packageId);
  if (tier === "premium") {
    return null;
  }
  const nicheKey = normalizeOrderNicheKey(niche) || flagshipNiche(tier, kind);
  const pool = vitrinePoolFor(tier, kind).map(vitrineDemoToSlide);
  const exact = nicheKey ? pool.find((s) => s.niche === nicheKey) : undefined;
  const picked = exact || pool[0] || null;
  return assertSlideMatchesTier(tier, picked);
}

/** Contextual demos for /order — product type + package + niche. */
export function resolveVitrinePreviewSlides(
  packageId: string | null | undefined,
  niche?: string | null,
  max = 6,
  kind: "website" | "store" = "website",
): PackagePreviewSlide[] {
  if (max <= 1) {
    const one = resolveExactOrderPreview(packageId, niche, kind);
    return one ? [one] : [];
  }
  const id = (packageId || "").toLowerCase();
  const nicheKey = normalizeOrderNicheKey(niche);
  const storeish =
    kind === "store" ||
    id.includes("store") ||
    id.includes("shop") ||
    id === "ai_store" ||
    id === "ecommerce_shop";
  const tier = normalizePreviewTier(packageId);
  const pool = vitrinePoolFor(tier, storeish ? "store" : "website");
  const slides = pool
    .map(vitrineDemoToSlide)
    .map((s) => assertSlideMatchesTier(tier, s))
    .filter((s): s is PackagePreviewSlide => Boolean(s));
  if (!nicheKey) return slides.slice(0, Math.min(max, 6));
  const preferred = slides.filter(
    (s) => s.niche === nicheKey || s.niche?.includes(nicheKey),
  );
  // Same package tier only — never pad with other packages.
  return preferred.slice(0, Math.min(max, 6));
}

/** basic_preview[] — Basic quality only (sites/basic). */
export const basic_preview: PackagePreviewSlide[] =
  PUBLIC_VITRINE_WEBSITES_BASIC.map(vitrineDemoToSlide);

/** business_preview[] — Business only */
export const business_preview: PackagePreviewSlide[] =
  PUBLIC_VITRINE_WEBSITES_BUSINESS.map(vitrineDemoToSlide);

/** premium_preview[] — empty until Premium product demos are ready. */
export const premium_preview: PackagePreviewSlide[] =
  PUBLIC_VITRINE_WEBSITES_PREMIUM.map(vitrineDemoToSlide);

/** premium_store_preview[] — empty until Premium shop demos are ready. */
export const premium_store_preview: PackagePreviewSlide[] =
  PUBLIC_VITRINE_STORES_PREMIUM.map(vitrineDemoToSlide);

export const PACKAGE_PREVIEW_GALLERY: Record<PackagePreviewTier, PackagePreviewSlide[]> = {
  basic: basic_preview,
  business: business_preview,
  premium: premium_preview,
};

/** Store demos for Business /site vitrine (cinematic shops). */
export const PACKAGE_STORE_PREVIEW_GALLERY: PackagePreviewSlide[] =
  PUBLIC_VITRINE_STORES_BUSINESS.map(vitrineDemoToSlide);

/** Default sample services shown in Premium block until the client enters their own. */
export const PREMIUM_SAMPLE_SERVICES: Record<string, string[]> = {
  auto: ["Diagnose", "Inspektion & Öl", "Bremsen", "Reifen"],
  dental: ["Prophylaxe", "Füllungen", "Ästhetik", "Implantate"],
  beauty: ["Maniküre & Pediküre", "Augenbrauen", "Wimpern", "Massage"],
  cleaning: ["Unterhaltsreinigung", "Büro", "Fenster", "Übergabe"],
  computer: ["Diagnose", "Reparatur", "Datenrettung", "Vor-Ort"],
  restaurant: ["Speisekarte", "Reservierung", "Mittagsmenü", "Events"],
  praxis: ["Erstberatung", "Therapie", "Nachsorge", "Online-Termin"],
  generic: ["Beratung", "Umsetzung", "Go-live", "Support"],
};

export function parseClientServices(raw: string | null | undefined): string[] {
  if (!raw?.trim()) return [];
  return raw
    .split(/[\n,;•·]+/)
    .map((s) => s.replace(/^[\s\-*]+/, "").trim())
    .filter((s) => s.length >= 2)
    .slice(0, 12);
}

export function resolvePremiumServices(
  niche: string | null | undefined,
  clientServices: string[] | null | undefined,
): string[] {
  if (clientServices && clientServices.length > 0) return clientServices.slice(0, 12);
  const key = (niche || "generic").trim().toLowerCase();
  return PREMIUM_SAMPLE_SERVICES[key] || PREMIUM_SAMPLE_SERVICES.generic;
}

export function normalizePreviewTier(packageId: string | null | undefined): PackagePreviewTier {
  const id = (packageId || "basic").toLowerCase();
  if (id === "connected" || id === "premium") return "premium";
  if (id === "standalone" || id === "business") return "business";
  if (id === "basic") return "basic";
  return "basic";
}

/**
 * Prefer /site vitrine SSOT (same thumbs + demos as the public gallery).
 * Niche match still reorders; tier arrays are fallback only if vitrine empty.
 */
export function resolvePackagePreviewSlides(
  packageId: string | null | undefined,
  niche?: string | null,
  max = 5,
  kind: "website" | "store" = "website",
): PackagePreviewSlide[] {
  const vitrine = resolveVitrinePreviewSlides(
    packageId,
    niche,
    Math.min(Math.max(max, 3), 6),
    kind,
  );
  if (vitrine.length > 0) return vitrine;

  const tier = normalizePreviewTier(packageId);
  const pool = (PACKAGE_PREVIEW_GALLERY[tier] || [])
    .map((s) => assertSlideMatchesTier(tier, s))
    .filter((s): s is PackagePreviewSlide => Boolean(s));
  const nicheKey = normalizeOrderNicheKey(niche);
  if (!nicheKey) return pool.slice(0, max);
  const preferred = pool.filter((s) => s.niche === nicheKey);
  // Same tier only — never pad Premium with Basic/Business or stores/premium legacy.
  return preferred.slice(0, max);
}

/** All gallery thumb paths the carousel may request (for deploy/self-check). */
export function allPackagePreviewImagePaths(): string[] {
  return [
    ...Object.values(PACKAGE_PREVIEW_GALLERY).flat(),
    ...PACKAGE_STORE_PREVIEW_GALLERY,
  ].map((s) => s.src);
}
