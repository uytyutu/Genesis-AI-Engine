/**
 * Package preview gallery — Path A order / storefront.
 * Each tier has exclusive full-site HTML samples (no cross-tier reuse).
 * Paths under /package-previews/sites/{tier}/{niche}/index.html
 */

export type PackagePreviewTier = "basic" | "business" | "premium";

export type PackagePreviewSlide = {
  /** Relative path under /package-previews/ */
  src: string;
  alt: string;
  niche?: string;
  /** Full landing sample (iframe), not a background photo */
  kind: "site";
};

/** basic_preview[] — Basic quality sites only */
export const basic_preview: PackagePreviewSlide[] = [
  {
    src: "sites/basic/auto/index.html",
    alt: "Autowerkstatt · Basic-Website",
    niche: "auto",
    kind: "site",
  },
  {
    src: "sites/basic/dental/index.html",
    alt: "Zahnarztpraxis · Basic-Website",
    niche: "dental",
    kind: "site",
  },
  {
    src: "sites/basic/beauty/index.html",
    alt: "Beauty · Basic-Website",
    niche: "beauty",
    kind: "site",
  },
];

/** business_preview[] — Business quality sites only */
export const business_preview: PackagePreviewSlide[] = [
  {
    src: "sites/business/auto/index.html",
    alt: "Autowerkstatt · Business-Website",
    niche: "auto",
    kind: "site",
  },
  {
    src: "sites/business/dental/index.html",
    alt: "Zahnarztpraxis · Business-Website",
    niche: "dental",
    kind: "site",
  },
  {
    src: "sites/business/praxis/index.html",
    alt: "Praxis · Business-Website",
    niche: "praxis",
    kind: "site",
  },
];

/** premium_preview[] — Premium quality sites only */
export const premium_preview: PackagePreviewSlide[] = [
  {
    src: "sites/premium/auto/index.html",
    alt: "Autowerkstatt · Premium-Website",
    niche: "auto",
    kind: "site",
  },
  {
    src: "sites/premium/dental/index.html",
    alt: "Zahnarztpraxis · Premium-Website",
    niche: "dental",
    kind: "site",
  },
  {
    src: "sites/premium/path/index.html",
    alt: "Premium-Website · Beispiel",
    niche: "path",
    kind: "site",
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

/** Prefer niche-matching slides, then fill — never mix tiers. */
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
