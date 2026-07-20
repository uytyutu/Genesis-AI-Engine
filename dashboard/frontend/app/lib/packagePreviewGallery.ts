/**
 * Package preview gallery — Path A order / storefront.
 * Each tier has exclusive hero screenshots (+ optional full HTML demo link).
 * Paths under /package-previews/sites/{tier}/{niche}/…
 */

export type PackagePreviewTier = "basic" | "business" | "premium";

export type PackagePreviewSlide = {
  /** Relative path under /package-previews/ — hero screenshot (always visible) */
  src: string;
  alt: string;
  niche?: string;
  /** Optional full HTML demo (opened in new tab, not iframe) */
  siteSrc?: string;
  kind: "image";
};

/** basic_preview[] — Basic quality sites only */
export const basic_preview: PackagePreviewSlide[] = [
  {
    src: "sites/basic/auto/assets/hero.jpg",
    siteSrc: "sites/basic/auto/index.html",
    alt: "Autowerkstatt · Basic-Website",
    niche: "auto",
    kind: "image",
  },
  {
    src: "sites/basic/dental/assets/hero.jpg",
    siteSrc: "sites/basic/dental/index.html",
    alt: "Zahnarztpraxis · Basic-Website",
    niche: "dental",
    kind: "image",
  },
  {
    src: "sites/basic/beauty/assets/hero.jpg",
    siteSrc: "sites/basic/beauty/index.html",
    alt: "Beauty · Basic-Website",
    niche: "beauty",
    kind: "image",
  },
];

/** business_preview[] — Business quality sites only */
export const business_preview: PackagePreviewSlide[] = [
  {
    src: "sites/business/auto/assets/hero.jpg",
    siteSrc: "sites/business/auto/index.html",
    alt: "Autowerkstatt · Business-Website",
    niche: "auto",
    kind: "image",
  },
  {
    src: "sites/business/dental/assets/hero.jpg",
    siteSrc: "sites/business/dental/index.html",
    alt: "Zahnarztpraxis · Business-Website",
    niche: "dental",
    kind: "image",
  },
  {
    src: "sites/business/praxis/assets/hero.jpg",
    siteSrc: "sites/business/praxis/index.html",
    alt: "Praxis · Business-Website",
    niche: "praxis",
    kind: "image",
  },
];

/** premium_preview[] — Premium quality sites only */
export const premium_preview: PackagePreviewSlide[] = [
  {
    src: "sites/premium/auto/assets/hero.jpg",
    siteSrc: "sites/premium/auto/index.html",
    alt: "Autowerkstatt · Premium-Website",
    niche: "auto",
    kind: "image",
  },
  {
    src: "sites/premium/dental/assets/hero.jpg",
    siteSrc: "sites/premium/dental/index.html",
    alt: "Zahnarztpraxis · Premium-Website",
    niche: "dental",
    kind: "image",
  },
  {
    src: "sites/premium/path/assets/hero.jpg",
    siteSrc: "sites/premium/path/index.html",
    alt: "Premium-Website · Beispiel",
    niche: "path",
    kind: "image",
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
