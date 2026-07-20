/**
 * Package preview gallery — Path A order / storefront.
 *
 * Production rule: every `src` must be a file under
 * `dashboard/frontend/public/package-previews/` that is **tracked in git**
 * and served as a public URL `/package-previews/...` (never a local disk path).
 *
 * `gallery.jpg` = compressed mobile/desktop thumbs (~40–90 KB).
 * Full demo HTML remains at `siteSrc` (open in new tab).
 */

export type PackagePreviewTier = "basic" | "business" | "premium";

export type PackagePreviewSlide = {
  /** Relative path under /package-previews/ */
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
    src: "sites/basic/auto/assets/gallery.jpg",
    siteSrc: "sites/basic/auto/index.html",
    alt: "Autowerkstatt · Basic-Website",
    niche: "auto",
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
    src: "sites/basic/beauty/assets/gallery.jpg",
    siteSrc: "sites/basic/beauty/index.html",
    alt: "Beauty · Basic-Website",
    niche: "beauty",
    kind: "image",
  },
];

/** business_preview[] — Business quality sites only */
export const business_preview: PackagePreviewSlide[] = [
  {
    src: "sites/business/auto/assets/gallery.jpg",
    siteSrc: "sites/business/auto/index.html",
    alt: "Autowerkstatt · Business-Website",
    niche: "auto",
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
    src: "sites/business/praxis/assets/gallery.jpg",
    siteSrc: "sites/business/praxis/index.html",
    alt: "Praxis · Business-Website",
    niche: "praxis",
    kind: "image",
  },
];

/** premium_preview[] — Premium quality sites only */
export const premium_preview: PackagePreviewSlide[] = [
  {
    src: "sites/premium/auto/assets/gallery.jpg",
    siteSrc: "sites/premium/auto/index.html",
    alt: "Autowerkstatt · Premium-Website",
    niche: "auto",
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
    src: "sites/premium/path/assets/gallery.jpg",
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

/** Default sample services shown in Premium block until the client enters their own. */
export const PREMIUM_SAMPLE_SERVICES: Record<string, string[]> = {
  auto: ["Diagnose", "Inspektion & Öl", "Bremsen", "Reifen"],
  dental: ["Prophylaxe", "Füllungen", "Ästhetik", "Implantate"],
  beauty: ["Schnitt & Styling", "Farbe", "Pflege", "Termin online"],
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

/** All gallery thumb paths the carousel may request (for deploy/self-check). */
export function allPackagePreviewImagePaths(): string[] {
  return Object.values(PACKAGE_PREVIEW_GALLERY)
    .flat()
    .map((s) => s.src);
}
