/**
 * Package preview gallery config — Path A order / storefront.
 * Paths are relative to backend /research-3d/ mount (_research_3d/).
 * Add slides here without touching carousel UI.
 */

export type PackagePreviewTier = "basic" | "business" | "premium";

export type PackagePreviewSlide = {
  /** Path under /research-3d/ */
  src: string;
  alt: string;
  /** Optional niche id for preferred ordering */
  niche?: string;
};

/** basic_preview[] */
export const basic_preview: PackagePreviewSlide[] = [
  {
    src: "showcases/auto/hero_pack/basic/hero_1.jpg",
    alt: "Autowerkstatt · Basic",
    niche: "auto",
  },
  {
    src: "showcases/dental/hero_pack/basic/hero_1.jpg",
    alt: "Zahnarzt · Basic",
    niche: "dental",
  },
  {
    src: "showcases/beauty/hero_pack/basic/hero_1.jpg",
    alt: "Beauty · Basic",
    niche: "beauty",
  },
  {
    src: "showcases/handwerk/hero_pack/basic/hero_1.jpg",
    alt: "Handwerk · Basic",
    niche: "handwerk",
  },
  {
    src: "showcases/generic/hero_pack/basic/hero_1.jpg",
    alt: "Business · Basic",
    niche: "generic",
  },
];

/** business_preview[] */
export const business_preview: PackagePreviewSlide[] = [
  {
    src: "showcases/auto/hero_pack/business/services.jpg",
    alt: "Autowerkstatt · Business",
    niche: "auto",
  },
  {
    src: "showcases/dental/hero_pack/business/services.jpg",
    alt: "Zahnarzt · Business",
    niche: "dental",
  },
  {
    src: "showcases/beauty/hero_pack/business/cta.jpg",
    alt: "Beauty · Business",
    niche: "beauty",
  },
  {
    src: "showcases/law/hero_pack/business/cta.jpg",
    alt: "Kanzlei · Business",
    niche: "law",
  },
  {
    src: "showcases/energy/hero_pack/business/hero_1.jpg",
    alt: "Energie · Business",
    niche: "energy",
  },
];

/** premium_preview[] */
export const premium_preview: PackagePreviewSlide[] = [
  {
    src: "showcases/dental/hero_pack/premium/showcase.jpg",
    alt: "Zahnarzt · Premium",
    niche: "dental",
  },
  {
    src: "showcases/auto/hero_pack/premium/banner.jpg",
    alt: "Autowerkstatt · Premium",
    niche: "auto",
  },
  {
    src: "showcases/beauty/hero_pack/premium/gallery.jpg",
    alt: "Beauty · Premium",
    niche: "beauty",
  },
  {
    src: "showcases/appliance/hero_pack/premium/showcase.jpg",
    alt: "Geräte · Premium",
    niche: "appliance",
  },
  {
    src: "showcases/green/hero_pack/premium/banner.jpg",
    alt: "Green · Premium",
    niche: "green",
  },
];

export const PACKAGE_PREVIEW_GALLERY: Record<PackagePreviewTier, PackagePreviewSlide[]> = {
  basic: basic_preview,
  business: business_preview,
  premium: premium_preview,
};

export function normalizePreviewTier(packageId: string | null | undefined): PackagePreviewTier {
  const id = (packageId || "basic").toLowerCase();
  if (id === "business" || id === "premium") return id;
  return "basic";
}

/** Prefer niche-matching slides, then fill up to max. */
export function resolvePackagePreviewSlides(
  packageId: string | null | undefined,
  niche?: string | null,
  max = 5,
): PackagePreviewSlide[] {
  const tier = normalizePreviewTier(packageId);
  const pool = PACKAGE_PREVIEW_GALLERY[tier] || [];
  const nicheKey = (niche || "").trim().toLowerCase();
  if (!nicheKey) return pool.slice(0, max);
  const preferred = pool.filter((s) => s.niche === nicheKey);
  const rest = pool.filter((s) => s.niche !== nicheKey);
  return [...preferred, ...rest].slice(0, max);
}
