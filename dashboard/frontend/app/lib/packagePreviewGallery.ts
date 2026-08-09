/**
 * Package preview gallery — Path A order / storefront.
 *
 * Order-form default slides use the same SSOT as /site vitrine:
 * `publicVitrineCatalog.ts` thumbs (`/vitrine/*.jpg`) + premium demos.
 *
 * Legacy tier arrays below remain for niche-specific fallbacks and deploy checks.
 * Absolute `/vitrine/...` src is allowed (see PackagePreviewCarousel.slideUrl).
 *
 * Owner niche rotation (2026-08): lead with Nail/Beauty · Cleaning · IT · Dental · Restaurant.
 * Do not default-showcase Autohaus.
 */

import {
  PUBLIC_VITRINE_EXAMPLES,
  PUBLIC_VITRINE_STORES,
  PUBLIC_VITRINE_THUMB_VERSION,
  PUBLIC_VITRINE_WEBSITES,
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
  const niche = demo.id.replace(/-store$/, "").replace(/_shop$/, "");
  return {
    src: `${demo.thumb}?v=${PUBLIC_VITRINE_THUMB_VERSION}`,
    siteSrc: demo.href.replace(/^\/package-previews\//, ""),
    alt: `${demo.fallback} · ${demo.kind === "store" ? "AI Store" : "Website"}`,
    niche,
    kind: "image",
  };
}

/** Same demos as /site#examples — used on order form preview. */
export function resolveVitrinePreviewSlides(
  packageId: string | null | undefined,
  niche?: string | null,
  max = 14,
): PackagePreviewSlide[] {
  const id = (packageId || "").toLowerCase();
  const nicheKey = (niche || "").trim().toLowerCase();
  const storeish =
    id.includes("store") || id.includes("shop") || id === "ai_store";
  const pool = storeish
    ? PUBLIC_VITRINE_STORES
    : id === "premium" || !nicheKey
      ? PUBLIC_VITRINE_EXAMPLES
      : PUBLIC_VITRINE_WEBSITES;
  const slides = pool.map(vitrineDemoToSlide);
  if (!nicheKey) return slides.slice(0, Math.max(max, pool.length));
  const preferred = slides.filter(
    (s) => s.niche === nicheKey || s.niche?.includes(nicheKey),
  );
  const rest = slides.filter((s) => !preferred.includes(s));
  return [...preferred, ...rest].slice(0, Math.max(max, 8));
}

/** basic_preview[] — Basic quality sites only */
export const basic_preview: PackagePreviewSlide[] = [
  {
    src: "sites/basic/beauty/assets/gallery.jpg",
    siteSrc: "sites/basic/beauty/index.html",
    alt: "Beauty · Basic-Website",
    niche: "beauty",
    kind: "image",
  },
  {
    src: "sites/basic/dental/assets/gallery.jpg",
    siteSrc: "sites/basic/dental/index.html",
    alt: "Zahnarztpraxis · Basic-Website",
    niche: "dental",
    kind: "image",
  },
  {
    src: "sites/basic/restaurant/assets/gallery.jpg",
    siteSrc: "sites/basic/restaurant/index.html",
    alt: "Restaurant · Basic-Website",
    niche: "restaurant",
    kind: "image",
  },
  {
    src: "sites/basic/auto/assets/gallery.jpg",
    siteSrc: "sites/basic/auto/index.html",
    alt: "Autowerkstatt · Basic-Website",
    niche: "auto",
    kind: "image",
  },
];

/** business_preview[] — Business quality sites only */
export const business_preview: PackagePreviewSlide[] = [
  {
    src: "sites/business/beauty/assets/gallery.jpg",
    siteSrc: "sites/business/beauty/index.html",
    alt: "Beauty · Business-Website",
    niche: "beauty",
    kind: "image",
  },
  {
    src: "sites/business/dental/assets/gallery.jpg",
    siteSrc: "sites/business/dental/index.html",
    alt: "Zahnarztpraxis · Business-Website",
    niche: "dental",
    kind: "image",
  },
  {
    src: "sites/business/restaurant/assets/gallery.jpg",
    siteSrc: "sites/business/restaurant/index.html",
    alt: "Restaurant · Business-Website",
    niche: "restaurant",
    kind: "image",
  },
  {
    src: "sites/business/it/assets/gallery.jpg",
    siteSrc: "sites/business/it/index.html",
    alt: "Computer-Reparatur · Business-Website",
    niche: "computer",
    kind: "image",
  },
  {
    src: "sites/business/handwerk/assets/gallery.jpg",
    siteSrc: "sites/business/handwerk/index.html",
    alt: "Handwerk · Business-Website",
    niche: "handwerk",
    kind: "image",
  },
  {
    src: "sites/business/law/assets/gallery.jpg",
    siteSrc: "sites/business/law/index.html",
    alt: "Kanzlei · Business-Website",
    niche: "law",
    kind: "image",
  },
  {
    src: "sites/business/auto/assets/gallery.jpg",
    siteSrc: "sites/business/auto/index.html",
    alt: "Autowerkstatt · Business-Website",
    niche: "auto",
    kind: "image",
  },
  {
    src: "sites/business/fitness/assets/gallery.jpg",
    siteSrc: "sites/business/fitness/index.html",
    alt: "Fitness · Business-Website",
    niche: "fitness",
    kind: "image",
  },
];

/** premium_preview[] — Premium quality sites (Factory / Owner demos, 3D where niche sells) */
export const premium_preview: PackagePreviewSlide[] = [
  {
    src: "sites/premium/beauty/assets/gallery.jpg",
    siteSrc: "sites/premium/beauty/index.html",
    alt: "Beauty · Premium-Website",
    niche: "beauty",
    kind: "image",
  },
  {
    src: "sites/premium/cleaning/assets/gallery.jpg",
    siteSrc: "sites/premium/cleaning/index.html",
    alt: "Reinigung · Premium-Website",
    niche: "cleaning",
    kind: "image",
  },
  {
    src: "sites/premium/dental/assets/gallery.jpg",
    siteSrc: "sites/premium/dental/index.html",
    alt: "Zahnarztpraxis · Premium-Website",
    niche: "dental",
    kind: "image",
  },
  {
    src: "sites/premium/restaurant/assets/gallery.jpg",
    siteSrc: "sites/premium/restaurant/index.html",
    alt: "Restaurant · Premium-Website",
    niche: "restaurant",
    kind: "image",
  },
  {
    src: "sites/premium/handwerk/assets/gallery.jpg",
    siteSrc: "sites/premium/handwerk/index.html",
    alt: "Handwerk · Premium-Website",
    niche: "handwerk",
    kind: "image",
  },
  {
    src: "sites/premium/law/assets/gallery.jpg",
    siteSrc: "sites/premium/law/index.html",
    alt: "Kanzlei · Premium-Website",
    niche: "law",
    kind: "image",
  },
  {
    src: "sites/premium/auto/assets/gallery.jpg",
    siteSrc: "sites/premium/auto/index.html",
    alt: "Autowerkstatt · Premium + 3D",
    niche: "auto",
    kind: "image",
  },
  {
    src: "sites/premium/car_dealership/assets/gallery.jpg",
    siteSrc: "sites/premium/car_dealership/index.html",
    alt: "Autohaus · Premium + 3D",
    niche: "car_dealership",
    kind: "image",
  },
  {
    src: "sites/premium/energy/assets/gallery.jpg",
    siteSrc: "sites/premium/energy/index.html",
    alt: "Solar / Energie · Premium + 3D",
    niche: "energy",
    kind: "image",
  },
  {
    src: "sites/premium/realestate/assets/gallery.jpg",
    siteSrc: "sites/premium/realestate/index.html",
    alt: "Immobilien · Premium-Website",
    niche: "realestate",
    kind: "image",
  },
  {
    src: "sites/premium/elektro/assets/gallery.jpg",
    siteSrc: "sites/premium/elektro/index.html",
    alt: "Elektro · Premium-Website",
    niche: "elektro",
    kind: "image",
  },
  {
    src: "sites/premium/fitness/assets/gallery.jpg",
    siteSrc: "sites/premium/fitness/index.html",
    alt: "Fitness · Premium-Website",
    niche: "fitness",
    kind: "image",
  },
  {
    src: "sites/premium/photography/assets/gallery.jpg",
    siteSrc: "sites/premium/photography/index.html",
    alt: "Fotografie · Premium-Website",
    niche: "photography",
    kind: "image",
  },
  {
    src: "sites/premium/maler/assets/gallery.jpg",
    siteSrc: "sites/premium/maler/index.html",
    alt: "Maler · Premium-Website",
    niche: "maler",
    kind: "image",
  },
  {
    src: "sites/premium/auto_detailing/assets/gallery.jpg",
    siteSrc: "sites/premium/auto_detailing/index.html",
    alt: "Auto Detailing · Premium + 3D",
    niche: "auto_detailing",
    kind: "image",
  },
];

/** premium_store_preview[] — 15 niche stores on the vitrine */
export const premium_store_preview: PackagePreviewSlide[] = [
  {
    src: "stores/premium/beauty/assets/images/hero.jpg",
    siteSrc: "stores/premium/beauty/catalog.html",
    alt: "Beauty Store · Premium",
    niche: "beauty",
    kind: "image",
  },
  {
    src: "stores/premium/fashion/assets/images/hero.jpg",
    siteSrc: "stores/premium/fashion/catalog.html",
    alt: "Fashion Store · Premium",
    niche: "fashion",
    kind: "image",
  },
  {
    src: "stores/premium/electronics/assets/images/hero.jpg",
    siteSrc: "stores/premium/electronics/catalog.html",
    alt: "Electronics Store · Premium",
    niche: "electronics",
    kind: "image",
  },
  {
    src: "stores/premium/furniture/assets/images/hero.jpg",
    siteSrc: "stores/premium/furniture/catalog.html",
    alt: "Möbel Store · Premium",
    niche: "furniture",
    kind: "image",
  },
  {
    src: "stores/premium/food/assets/images/hero.jpg",
    siteSrc: "stores/premium/food/catalog.html",
    alt: "Food Store · Premium",
    niche: "food",
    kind: "image",
  },
  {
    src: "stores/premium/handwerk/assets/images/hero.jpg",
    siteSrc: "stores/premium/handwerk/catalog.html",
    alt: "Handwerk Shop · Premium",
    niche: "handwerk",
    kind: "image",
  },
  {
    src: "stores/premium/psychology/assets/images/hero.jpg",
    siteSrc: "stores/premium/psychology/catalog.html",
    alt: "Psychology Digital Store · Premium",
    niche: "psychology",
    kind: "image",
  },
  {
    src: "stores/premium/jewelry/assets/images/hero.jpg",
    siteSrc: "stores/premium/jewelry/catalog.html",
    alt: "Jewelry Store · Premium",
    niche: "jewelry",
    kind: "image",
  },
  {
    src: "stores/premium/cleaning_shop/assets/images/hero.jpg",
    siteSrc: "stores/premium/cleaning_shop/catalog.html",
    alt: "Cleaning Shop · Premium",
    niche: "cleaning",
    kind: "image",
  },
  {
    src: "stores/premium/detailing_shop/assets/images/hero.jpg",
    siteSrc: "stores/premium/detailing_shop/catalog.html",
    alt: "Detailing Shop · Premium + 3D",
    niche: "auto_detailing",
    kind: "image",
  },
  {
    src: "stores/premium/solar_shop/assets/images/hero.jpg",
    siteSrc: "stores/premium/solar_shop/catalog.html",
    alt: "Solar Shop · Premium + 3D",
    niche: "energy",
    kind: "image",
  },
  {
    src: "stores/premium/auto_parts/assets/images/hero.jpg",
    siteSrc: "stores/premium/auto_parts/catalog.html",
    alt: "Auto Parts · Premium",
    niche: "auto",
    kind: "image",
  },
  {
    src: "stores/premium/wine_shop/assets/images/hero.jpg",
    siteSrc: "stores/premium/wine_shop/catalog.html",
    alt: "Wine Shop · Premium",
    niche: "food",
    kind: "image",
  },
  {
    src: "stores/premium/bookstore/assets/images/hero.jpg",
    siteSrc: "stores/premium/bookstore/catalog.html",
    alt: "Bookstore · Premium",
    niche: "books",
    kind: "image",
  },
  {
    src: "stores/premium/coffee/assets/images/hero.jpg",
    siteSrc: "stores/premium/coffee/catalog.html",
    alt: "Coffee Store · Premium",
    niche: "coffee",
    kind: "image",
  },
];

export const PACKAGE_PREVIEW_GALLERY: Record<PackagePreviewTier, PackagePreviewSlide[]> = {
  basic: basic_preview,
  business: business_preview,
  premium: premium_preview,
};

/** Store demos for Premium /site vitrine (separate from website carousel). */
export const PACKAGE_STORE_PREVIEW_GALLERY: PackagePreviewSlide[] = premium_store_preview;

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
  if (id === "business" || id === "premium") return id;
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
): PackagePreviewSlide[] {
  const vitrine = resolveVitrinePreviewSlides(packageId, niche, Math.max(max, 14));
  if (vitrine.length > 0) return vitrine.slice(0, Math.max(max, vitrine.length));

  const tier = normalizePreviewTier(packageId);
  const pool = PACKAGE_PREVIEW_GALLERY[tier] || [];
  const nicheKey = (niche || "").trim().toLowerCase();
  if (tier === "premium" && !nicheKey) {
    const sites = premium_preview;
    const stores = premium_store_preview;
    const interleaved: PackagePreviewSlide[] = [];
    const n = Math.max(sites.length, stores.length);
    for (let i = 0; i < n; i += 1) {
      if (i < sites.length) interleaved.push(sites[i]!);
      if (i < stores.length) interleaved.push(stores[i]!);
    }
    return interleaved.slice(0, Math.max(max, 10));
  }
  if (!nicheKey) return pool.slice(0, max);
  const preferred = pool.filter((s) => s.niche === nicheKey);
  const rest = pool.filter((s) => s.niche !== nicheKey);
  const withStores =
    tier === "premium"
      ? [
          ...preferred,
          ...premium_store_preview.filter((s) => s.niche === nicheKey),
          ...rest,
          ...premium_store_preview.filter((s) => s.niche !== nicheKey),
        ]
      : [...preferred, ...rest];
  return withStores.slice(0, max);
}

/** All gallery thumb paths the carousel may request (for deploy/self-check). */
export function allPackagePreviewImagePaths(): string[] {
  return [
    ...Object.values(PACKAGE_PREVIEW_GALLERY).flat(),
    ...PACKAGE_STORE_PREVIEW_GALLERY,
  ].map((s) => s.src);
}
