/**
 * Public /site vitrine — Basic / Business live (2026-08-12).
 *
 * Sellable reality now:
 *   Basic    = sites/basic + stores/basic (standard delivery)
 *   Business = cinematic flagships under package-previews/premium/ (Workspace tier)
 *   Premium  = not ready yet → empty showcase (no fake Premium demos)
 *
 * Folder name `/premium/` on disk is historical path for cinematic assets —
 * packageId on the vitrine is the SSOT for which package they sell.
 *
 * Quarantined leftovers stay under:
 *   public/package-previews/legacy/quarantine/
 * Do not link random quarantine paths — only restored live Basic folders.
 */

export type PublicVitrineKind = "website" | "store";
export type PublicVitrinePackage = "basic" | "business" | "premium";
export type ShowcaseStatus = "PUBLISHED" | "QUARANTINED" | "REWORK_REQUIRED";

export type PublicVitrineDemo = {
  id: string;
  niche: string;
  kind: PublicVitrineKind;
  packageId: PublicVitrinePackage;
  href: string;
  thumb: string;
  emoji: string;
  labelKey: string;
  fallback: string;
  blurb: string;
  priceKind: "website" | "store";
  badge?: string;
  /** Only PUBLISHED may appear on public surfaces */
  showcaseStatus: ShowcaseStatus;
};

/** Niches reserved for future equal-count rebuild. */
export const WEBSITE_EXAMPLE_NICHES = [
  { id: "dental", folder: "dental", emoji: "🦷", labelKey: "examples.dental", fallback: "Zahnarzt", blurb: "Praxis & Termin" },
  { id: "beauty", folder: "beauty", emoji: "💅", labelKey: "examples.beauty", fallback: "Beauty Studio", blurb: "Salon & Pflege" },
  { id: "restaurant", folder: "restaurant", emoji: "🍽", labelKey: "examples.restaurant", fallback: "Restaurant", blurb: "Menü & Reservierung" },
  { id: "law", folder: "law", emoji: "⚖️", labelKey: "examples.law", fallback: "Rechtsanwalt", blurb: "Bereiche & Kontakt" },
  { id: "auto", folder: "auto", emoji: "🔧", labelKey: "examples.auto", fallback: "Autowerkstatt", blurb: "Service & Termin" },
  { id: "handwerk", folder: "handwerk", emoji: "🔨", labelKey: "examples.handwerk", fallback: "Handwerk", blurb: "Projekte & Angebot" },
  { id: "barbershop", folder: "barbershop", emoji: "💈", labelKey: "examples.barbershop", fallback: "Barbershop", blurb: "Schnitt & Style" },
  { id: "gartenpflege", folder: "gartenpflege", emoji: "🌿", labelKey: "examples.gartenpflege", fallback: "Gartenpflege", blurb: "Garten & Pflege" },
  { id: "dachreinigung", folder: "dachreinigung", emoji: "🏠", labelKey: "examples.dachreinigung", fallback: "Dachreinigung", blurb: "Reinigung & Service" },
  { id: "zaunbau", folder: "zaunbau", emoji: "🪵", labelKey: "examples.zaunbau", fallback: "Zaunbau", blurb: "Zaun & Montage" },
] as const;

export const STORE_EXAMPLE_NICHES = [
  { id: "fashion", folder: "fashion", emoji: "👗", labelKey: "examples.fashionStore", fallback: "Fashion Store", blurb: "Katalog & Warenkorb" },
  { id: "electronics", folder: "electronics", emoji: "🔌", labelKey: "examples.electronicsStore", fallback: "Electronics Store", blurb: "Geräte & Specs" },
  { id: "beauty", folder: "beauty", emoji: "🧴", labelKey: "examples.beautyStore", fallback: "Beauty Store", blurb: "Pflege & Bundles" },
  { id: "food", folder: "food", emoji: "🛒", labelKey: "examples.foodStore", fallback: "Food Store", blurb: "Produkte & Checkout" },
  { id: "furniture", folder: "furniture", emoji: "🪑", labelKey: "examples.furnitureStore", fallback: "Furniture Store", blurb: "Möbel & Räume" },
  { id: "accessories", folder: "accessories", emoji: "👜", labelKey: "examples.accessoriesStore", fallback: "Accessories Store", blurb: "Accessoires" },
  { id: "handwerk", folder: "handwerk", emoji: "🛠", labelKey: "examples.handwerkStore", fallback: "Handwerk Shop", blurb: "Material & Shop" },
  { id: "gartenpflege", folder: "gartenpflege", emoji: "🌱", labelKey: "examples.gartenStore", fallback: "Garten Shop", blurb: "Pflanzen & Pflege" },
  { id: "dachreinigung", folder: "dachreinigung", emoji: "🏠", labelKey: "examples.dachreinigungStore", fallback: "Dach Shop", blurb: "Reinigung & Shop" },
  { id: "zaunbau", folder: "zaunbau", emoji: "🪵", labelKey: "examples.zaunbauStore", fallback: "Zaunbau Shop", blurb: "Zaunsysteme" },
] as const;

/** Basic websites — restored live paths (not quarantine links). */
export const PUBLIC_VITRINE_WEBSITES_BASIC: PublicVitrineDemo[] = [
  {
    id: "web-basic-beauty",
    niche: "beauty",
    kind: "website",
    packageId: "basic",
    href: "/package-previews/sites/basic/beauty/index.html",
    thumb: "/package-previews/sites/basic/beauty/assets/hero.jpg",
    emoji: "💅",
    labelKey: "examples.beauty",
    fallback: "Beauty Studio",
    blurb: "Salon & Pflege",
    priceKind: "website",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "web-basic-barbershop",
    niche: "barbershop",
    kind: "website",
    packageId: "basic",
    href: "/package-previews/sites/basic/barbershop/index.html",
    thumb: "/package-previews/sites/basic/barbershop/assets/hero.jpg",
    emoji: "💈",
    labelKey: "examples.barbershop",
    fallback: "Barbershop",
    blurb: "Schnitt & Style",
    priceKind: "website",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "web-basic-restaurant",
    niche: "restaurant",
    kind: "website",
    packageId: "basic",
    href: "/package-previews/sites/basic/restaurant/index.html",
    thumb: "/package-previews/sites/basic/restaurant/assets/hero.jpg",
    emoji: "🍽",
    labelKey: "examples.restaurant",
    fallback: "Restaurant",
    blurb: "Menü & Reservierung",
    priceKind: "website",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "web-basic-auto",
    niche: "auto",
    kind: "website",
    packageId: "basic",
    href: "/package-previews/sites/basic/auto/index.html",
    thumb: "/package-previews/sites/basic/auto/assets/hero.jpg",
    emoji: "🔧",
    labelKey: "examples.auto",
    fallback: "Autowerkstatt",
    blurb: "Service & Termin",
    priceKind: "website",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
];

/**
 * Business websites — cinematic flagships (disk path still under /premium/).
 * These are the sellable Business examples, not Premium (Premium not ready).
 */
export const PUBLIC_VITRINE_WEBSITES_BUSINESS: PublicVitrineDemo[] = [
  {
    id: "web-business-automotive",
    niche: "automotive",
    kind: "website",
    packageId: "business",
    href: "/package-previews/premium/luxury-automotive/index.html",
    thumb: "/package-previews/premium/luxury-automotive/assets/seq/f001.jpg",
    emoji: "🚗",
    labelKey: "examples.auto",
    fallback: "Luxury Automotive",
    blurb: "Business-Präsentation",
    priceKind: "website",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "web-business-restaurant",
    niche: "restaurant",
    kind: "website",
    packageId: "business",
    href: "/package-previews/premium/hot-dog/index.html",
    thumb: "/package-previews/premium/hot-dog/assets/seq/f001.jpg",
    emoji: "🌭",
    labelKey: "examples.restaurant",
    fallback: "Hot Dog · Restaurant",
    blurb: "Business-Präsentation",
    priceKind: "website",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "web-business-beauty",
    niche: "beauty",
    kind: "website",
    packageId: "business",
    href: "/package-previews/premium/beauty-brows/index.html",
    thumb: "/package-previews/premium/beauty-brows/assets/seq/f001.jpg",
    emoji: "💅",
    labelKey: "examples.beauty",
    fallback: "Beauty Studio",
    blurb: "Business-Präsentation",
    priceKind: "website",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "web-business-barbershop",
    niche: "barbershop",
    kind: "website",
    packageId: "business",
    href: "/package-previews/premium/barbershop/index.html",
    thumb: "/package-previews/premium/barbershop/assets/seq/f001.jpg",
    emoji: "💈",
    labelKey: "examples.barbershop",
    fallback: "Barbershop",
    blurb: "Business-Präsentation",
    priceKind: "website",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
];

/** Premium websites — not ready; no public demos. */
export const PUBLIC_VITRINE_WEBSITES_PREMIUM: PublicVitrineDemo[] = [];

export const PUBLIC_VITRINE_STORES_BASIC: PublicVitrineDemo[] = [
  {
    id: "shop-basic-fashion",
    niche: "fashion",
    kind: "store",
    packageId: "basic",
    href: "/package-previews/stores/basic/fashion/index.html",
    thumb: "/package-previews/stores/basic/fashion/assets/images/hero.jpg",
    emoji: "👗",
    labelKey: "examples.fashionStore",
    fallback: "Fashion Store",
    blurb: "Katalog & Warenkorb",
    priceKind: "store",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "shop-basic-electronics",
    niche: "electronics",
    kind: "store",
    packageId: "basic",
    href: "/package-previews/stores/basic/electronics/index.html",
    thumb: "/package-previews/stores/basic/electronics/assets/images/hero.jpg",
    emoji: "🔌",
    labelKey: "examples.electronicsStore",
    fallback: "Electronics Store",
    blurb: "Geräte & Specs",
    priceKind: "store",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "shop-basic-food",
    niche: "food",
    kind: "store",
    packageId: "basic",
    href: "/package-previews/stores/basic/food/index.html",
    thumb: "/package-previews/stores/basic/food/assets/images/hero.jpg",
    emoji: "🛒",
    labelKey: "examples.foodStore",
    fallback: "Food Store",
    blurb: "Produkte & Checkout",
    priceKind: "store",
    badge: "Basic",
    showcaseStatus: "PUBLISHED",
  },
];

export const PUBLIC_VITRINE_STORES_BUSINESS: PublicVitrineDemo[] = [
  {
    id: "shop-business-food",
    niche: "food",
    kind: "store",
    packageId: "business",
    href: "/package-previews/premium/shop-food/index.html",
    thumb: "/package-previews/premium/shop-food/assets/seq/f001.jpg",
    emoji: "🌭",
    labelKey: "examples.foodStore",
    fallback: "Food Store",
    blurb: "Business-Shop-Präsentation",
    priceKind: "store",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "shop-business-fashion",
    niche: "fashion",
    kind: "store",
    packageId: "business",
    href: "/package-previews/premium/shop-fashion-v2/index.html",
    thumb: "/package-previews/premium/shop-fashion-v2/assets/cinematic/c001.jpg",
    emoji: "👗",
    labelKey: "examples.fashionStore",
    fallback: "Fashion Store",
    blurb: "Business-Shop-Präsentation",
    priceKind: "store",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
  {
    id: "shop-business-electronics",
    niche: "electronics",
    kind: "store",
    packageId: "business",
    href: "/package-previews/premium/shop-electronics/index.html",
    thumb: "/package-previews/premium/shop-electronics/assets/seq/f001.jpg",
    emoji: "🔌",
    labelKey: "examples.electronicsStore",
    fallback: "Electronics Store",
    blurb: "Business-Shop-Präsentation",
    priceKind: "store",
    badge: "Business",
    showcaseStatus: "PUBLISHED",
  },
];

/** Premium stores — not ready. */
export const PUBLIC_VITRINE_STORES_PREMIUM: PublicVitrineDemo[] = [];

export const PACKAGE_EXAMPLE_COUNT = Math.max(
  PUBLIC_VITRINE_WEBSITES_BASIC.length,
  PUBLIC_VITRINE_WEBSITES_BUSINESS.length,
);

export const PUBLIC_VITRINE_WEBSITES: PublicVitrineDemo[] = [
  ...PUBLIC_VITRINE_WEBSITES_BASIC,
  ...PUBLIC_VITRINE_WEBSITES_BUSINESS,
  ...PUBLIC_VITRINE_WEBSITES_PREMIUM,
];

export const PUBLIC_VITRINE_STORES: PublicVitrineDemo[] = [
  ...PUBLIC_VITRINE_STORES_BASIC,
  ...PUBLIC_VITRINE_STORES_BUSINESS,
  ...PUBLIC_VITRINE_STORES_PREMIUM,
];

export const PUBLIC_VITRINE_EXAMPLES: PublicVitrineDemo[] = [
  ...PUBLIC_VITRINE_WEBSITES,
  ...PUBLIC_VITRINE_STORES,
];

export const SHOWCASE_QUALITY_RESET_NOTE =
  "Premium-Beispiele noch nicht freigegeben. Basic und Business zeigen echte Paket-Demos.";

export const SHOWCASE_PREMIUM_NOT_READY_NOTE =
  "Premium ist noch nicht bereit — Beispiele folgen nach Quality Gate. Bestellen Sie Basic oder Business.";

export type PackageIncludesBlock = {
  packageId: PublicVitrinePackage;
  kind: PublicVitrineKind;
  priceLabel: string;
  includes: string[];
  virtusControl: boolean;
  controlLines: string[];
};

export const WEBSITE_PACKAGE_INCLUDES: PackageIncludesBlock[] = [
  {
    packageId: "basic",
    kind: "website",
    priceLabel: "299 €",
    virtusControl: false,
    includes: [
      "Moderne professionelle Website für Ihre Branche",
      "Responsive Design",
      "Kontakt & Impressum-Struktur",
      "SEO-Grundlage",
      "Übergabe als fertiges Projekt",
    ],
    controlLines: ["Kein Virtus Steuerungs-Panel (Änderungen über Auftrag/Support)"],
  },
  {
    packageId: "business",
    kind: "website",
    priceLabel: "599 €",
    virtusControl: true,
    includes: [
      "Alles aus Basic",
      "Präsentations-/cinematic Niveau",
      "Virtus Client Workspace",
      "Inhalte, Texte, Medien selbst ändern",
      "Analytics-Grundlage",
    ],
    controlLines: [
      "Texte & Beschreibungen bearbeiten",
      "Bilder hochladen / ersetzen",
      "Sektionen ein-/ausblenden",
      "Versionen wiederherstellen",
    ],
  },
  {
    packageId: "premium",
    kind: "website",
    priceLabel: "999 €",
    virtusControl: true,
    includes: [
      "Alles aus Business — gleiche visuelle Qualität",
      "Erweiterte Website-Steuerung",
      "Tiefere Seitenstruktur",
      "Erweiterte Formulare & Content",
      "Fortgeschrittenes Management",
    ],
    controlLines: [
      "Alles aus Business-Steuerung",
      "Mehr Seiten / feinere Struktur",
      "Erweiterte Formulare & Content-Blöcke",
      "Fortgeschrittenes Management & Restore",
    ],
  },
];

export const STORE_PACKAGE_INCLUDES: PackageIncludesBlock[] = [
  {
    packageId: "basic",
    kind: "store",
    priceLabel: "Online Store · Start",
    virtusControl: false,
    includes: [
      "Eigenes Produkt: Online-Shop (nicht Website-Paket)",
      "Katalog, Produktseiten & Preise",
      "Warenkorb / Bestellweg",
      "Responsive Shop-Design",
    ],
    controlLines: ["Kein volles Virtus Shop-Admin (Änderungen über Auftrag/Support)"],
  },
  {
    packageId: "business",
    kind: "store",
    priceLabel: "Online Store · Business",
    virtusControl: true,
    includes: [
      "Alles aus Start",
      "Virtus Shop Admin",
      "Produkte · Kategorien · Bestellungen",
      "Hochwertige Produktpräsentation",
      "Kunden & Commerce-Grundlage",
    ],
    controlLines: [
      "Produkte anlegen / bearbeiten / soft-delete",
      "Preise, Texte, Bilder, Varianten",
      "Kategorien verwalten",
      "Bestellungen einsehen",
      "Versionen / Restore",
    ],
  },
  {
    packageId: "premium",
    kind: "store",
    priceLabel: "Online Store · Premium",
    virtusControl: true,
    includes: [
      "Alles aus Store Business — gleiche visuelle Qualität",
      "Erweiterte Shop-Steuerung & Analytics",
      "Tiefere Katalog-/Content-Struktur",
      "Fortgeschrittenes Bestell- und Media-Management",
    ],
    controlLines: [
      "Alles aus Business-Admin",
      "Erweiterte Katalog- und Content-Tiefe",
      "Design / Hero / Media Steuerung",
      "Restore Original / Versionen",
    ],
  },
];

export const PUBLIC_VITRINE_LEGACY_BLOCKLIST = [
  "/package-previews/legacy/quarantine/",
  "/package-previews/client-forms/",
  "/package-previews/sites/premium/",
  "/package-previews/stores/premium/",
  "/package-previews/sites/_trash_family/",
  "family_care",
  "Family Care",
  "family_psychology",
  "shop-*-parity",
] as const;

/** Cinematic Business demos still live under disk folder /premium/. */
const BUSINESS_CINEMATIC_HREFS = [
  "/package-previews/premium/luxury-automotive/",
  "/package-previews/premium/hot-dog/",
  "/package-previews/premium/beauty-brows/",
  "/package-previews/premium/barbershop/",
  "/package-previews/premium/shop-food/",
  "/package-previews/premium/shop-fashion-v2/",
  "/package-previews/premium/shop-electronics/",
] as const;

export const PUBLIC_VITRINE_THUMB_VERSION = "v22basicBusiness";

export function isPublishedShowcaseDemo(demo: PublicVitrineDemo): boolean {
  return demo.showcaseStatus === "PUBLISHED";
}

export function isLegacyPublicPreview(href: string): boolean {
  const h = href.replace(/\\/g, "/").toLowerCase();
  if (h.includes("/legacy/quarantine/")) return true;
  if (h.includes("/sites/premium/") || h.includes("/stores/premium/")) return true;
  if (h.includes("-parity/") || h.includes("beauty-studio") || h.includes("/psychology/")) {
    return true;
  }
  return PUBLIC_VITRINE_LEGACY_BLOCKLIST.some((p) => {
    if (p.includes("*")) return false;
    return h.includes(p.toLowerCase());
  });
}

export function allPublicVitrineHrefs(): string[] {
  return PUBLIC_VITRINE_EXAMPLES.filter(isPublishedShowcaseDemo).map((d) => d.href);
}

export function allPublicVitrineThumbs(): string[] {
  return PUBLIC_VITRINE_EXAMPLES.filter(isPublishedShowcaseDemo).map((d) => d.thumb);
}

/** Integrity: Basic/Business published correctly; Premium empty until ready. */
export function assertShowcaseIntegrity(): boolean {
  const live = PUBLIC_VITRINE_EXAMPLES.filter(isPublishedShowcaseDemo);
  if (live.some((d) => isLegacyPublicPreview(d.href))) return false;
  if (PUBLIC_VITRINE_WEBSITES_PREMIUM.length !== 0) return false;
  if (PUBLIC_VITRINE_STORES_PREMIUM.length !== 0) return false;
  if (live.some((d) => d.packageId === "premium")) return false;
  if (!live.every((d) => d.packageId === "basic" || d.packageId === "business")) return false;
  if (!PUBLIC_VITRINE_WEBSITES_BASIC.every((d) => isBasicStandardHref(d.href))) return false;
  if (!PUBLIC_VITRINE_STORES_BASIC.every((d) => isBasicStandardHref(d.href))) return false;
  if (!PUBLIC_VITRINE_WEBSITES_BUSINESS.every((d) => isBusinessHref(d.href))) return false;
  if (!PUBLIC_VITRINE_STORES_BUSINESS.every((d) => isBusinessHref(d.href))) return false;
  return live.length > 0;
}

/** @deprecated Use assertShowcaseIntegrity */
export function assertEqualPackageExampleCounts(): boolean {
  return assertShowcaseIntegrity();
}

/** True Premium cinematic (none published yet). */
export function isPremiumCinematicHref(href: string): boolean {
  void href;
  return false;
}

export function isBasicStandardHref(href: string): boolean {
  const h = href.replace(/\\/g, "/");
  if (isLegacyPublicPreview(h)) return false;
  return (
    (h.includes("/package-previews/sites/basic/") ||
      h.includes("/package-previews/stores/basic/")) &&
    !h.includes("/legacy/")
  );
}

export function isBusinessHref(href: string): boolean {
  const h = href.replace(/\\/g, "/");
  if (isLegacyPublicPreview(h)) return false;
  if (h.includes("/package-previews/sites/business/") || h.includes("/package-previews/stores/business/")) {
    return true;
  }
  return BUSINESS_CINEMATIC_HREFS.some((p) => h.includes(p));
}
