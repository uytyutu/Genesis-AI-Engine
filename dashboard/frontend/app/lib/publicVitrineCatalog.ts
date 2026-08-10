/**
 * Public /site vitrine — examples grouped by PACKAGE (not niche-only).
 *
 * Basic  = earliest simple demos (sites|stores/basic) — one-hero standard pages.
 * Business / Premium = newer demos with generated media + cinematic scroll
 *   (sites|stores/premium folders + live cinematic showcases).
 * Premium leads with cinematic ACTION→TRANSFORM→RESULT demos.
 */

export type PublicVitrineKind = "website" | "store";
export type PublicVitrinePackage = "basic" | "business" | "premium";

export type PublicVitrineDemo = {
  id: string;
  /** Niche key for order-form gallery matching (e.g. dental, fashion) */
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
};

/** Same 10 niches for Website Basic · Business · Premium */
export const WEBSITE_EXAMPLE_NICHES = [
  { id: "dental", folder: "dental", emoji: "🦷", labelKey: "examples.dental", fallback: "Zahnarzt", blurb: "Praxis & Termin" },
  { id: "beauty", folder: "beauty", emoji: "💅", labelKey: "examples.beauty", fallback: "Beauty Studio", blurb: "Salon & Pflege" },
  { id: "restaurant", folder: "restaurant", emoji: "🍽", labelKey: "examples.restaurant", fallback: "Restaurant", blurb: "Menü & Reservierung" },
  { id: "law", folder: "law", emoji: "⚖️", labelKey: "examples.law", fallback: "Rechtsanwalt", blurb: "Bereiche & Kontakt" },
  { id: "auto", folder: "auto", emoji: "🔧", labelKey: "examples.auto", fallback: "Autowerkstatt", blurb: "Service & Termin" },
  { id: "handwerk", folder: "handwerk", emoji: "🔨", labelKey: "examples.handwerk", fallback: "Handwerk", blurb: "Projekte & Angebot" },
  { id: "psychology", folder: "psychology", emoji: "🧠", labelKey: "examples.psychology", fallback: "Psychologie", blurb: "Praxis & Erstgespräch" },
  { id: "gartenpflege", folder: "gartenpflege", emoji: "🌿", labelKey: "examples.gartenpflege", fallback: "Gartenpflege", blurb: "Garten & Pflege" },
  { id: "dachreinigung", folder: "dachreinigung", emoji: "🏠", labelKey: "examples.dachreinigung", fallback: "Dachreinigung", blurb: "Reinigung & Service" },
  { id: "zaunbau", folder: "zaunbau", emoji: "🪵", labelKey: "examples.zaunbau", fallback: "Zaunbau", blurb: "Zaun & Montage" },
] as const;

/** Same 10 niches for Online-Shop Basic · Business · Premium */
export const STORE_EXAMPLE_NICHES = [
  { id: "fashion", folder: "fashion", emoji: "👗", labelKey: "examples.fashionStore", fallback: "Fashion Store", blurb: "Katalog & Warenkorb" },
  { id: "electronics", folder: "electronics", emoji: "🔌", labelKey: "examples.electronicsStore", fallback: "Electronics Store", blurb: "Geräte & Specs" },
  { id: "beauty", folder: "beauty", emoji: "🧴", labelKey: "examples.beautyStore", fallback: "Beauty Store", blurb: "Pflege & Bundles" },
  { id: "food", folder: "food", emoji: "🛒", labelKey: "examples.foodStore", fallback: "Food Store", blurb: "Produkte & Checkout" },
  { id: "furniture", folder: "furniture", emoji: "🪑", labelKey: "examples.furnitureStore", fallback: "Furniture Store", blurb: "Möbel & Räume" },
  { id: "accessories", folder: "accessories", emoji: "👜", labelKey: "examples.accessoriesStore", fallback: "Accessories Store", blurb: "Accessoires" },
  { id: "handwerk", folder: "handwerk", emoji: "🛠", labelKey: "examples.handwerkStore", fallback: "Handwerk Shop", blurb: "Material & Shop" },
  { id: "gartenpflege", folder: "gartenpflege", emoji: "🌱", labelKey: "examples.gartenStore", fallback: "Garten Shop", blurb: "Pflanzen & Pflege" },
  { id: "psychology", folder: "psychology", emoji: "📚", labelKey: "examples.psychologyStore", fallback: "Psychology Shop", blurb: "Kurse & Produkte" },
  { id: "zaunbau", folder: "zaunbau", emoji: "🪵", labelKey: "examples.zaunbauStore", fallback: "Zaunbau Shop", blurb: "Zaunsysteme" },
] as const;

export const PACKAGE_EXAMPLE_COUNT = WEBSITE_EXAMPLE_NICHES.length;

/**
 * Folder mapping:
 * - basic → sites|stores/basic (early simple)
 * - business + premium → sites|stores/premium (newer generated media)
 *   Premium additionally prepends live cinematic demos.
 */
function demoFolderForPackage(pkg: PublicVitrinePackage): "basic" | "premium" {
  return pkg === "basic" ? "basic" : "premium";
}

function websiteHref(pkg: PublicVitrinePackage, folder: string): string {
  const dir = demoFolderForPackage(pkg);
  return `/package-previews/sites/${dir}/${folder}/index.html`;
}

function storeHref(pkg: PublicVitrinePackage, folder: string): string {
  const dir = demoFolderForPackage(pkg);
  if (dir === "basic") {
    return `/package-previews/stores/basic/${folder}/index.html`;
  }
  return `/package-previews/stores/premium/${folder}/catalog.html`;
}

function thumbForWebsite(pkg: PublicVitrinePackage, folder: string): string {
  const dir = demoFolderForPackage(pkg);
  return `/package-previews/sites/${dir}/${folder}/assets/hero.jpg`;
}

function thumbForStore(pkg: PublicVitrinePackage, folder: string): string {
  const dir = demoFolderForPackage(pkg);
  return `/package-previews/stores/${dir}/${folder}/assets/images/hero.jpg`;
}

function buildWebsitePackage(pkg: PublicVitrinePackage): PublicVitrineDemo[] {
  return WEBSITE_EXAMPLE_NICHES.map((n) => ({
    id: `web-${pkg}-${n.id}`,
    niche: n.id,
    kind: "website" as const,
    packageId: pkg,
    href: websiteHref(pkg, n.folder),
    thumb: thumbForWebsite(pkg, n.folder),
    emoji: n.emoji,
    labelKey: n.labelKey,
    fallback: n.fallback,
    blurb: pkg === "basic" ? n.blurb : `${n.blurb} · Studio`,
    priceKind: "website" as const,
    badge: pkg === "premium" ? "Premium" : pkg === "business" ? "Business" : "Basic",
  }));
}

function buildStorePackage(pkg: PublicVitrinePackage): PublicVitrineDemo[] {
  return STORE_EXAMPLE_NICHES.map((n) => ({
    id: `shop-${pkg}-${n.id}`,
    niche: n.id,
    kind: "store" as const,
    packageId: pkg,
    href: storeHref(pkg, n.folder),
    thumb: thumbForStore(pkg, n.folder),
    emoji: n.emoji,
    labelKey: n.labelKey,
    fallback: n.fallback,
    blurb: pkg === "basic" ? n.blurb : `${n.blurb} · Studio`,
    priceKind: "store" as const,
    badge: pkg === "premium" ? "Premium" : pkg === "business" ? "Business" : "Basic",
  }));
}

/** Cinematic scroll demos — Business + Premium (never Basic). */
export const PUBLIC_VITRINE_CINEMATIC_WEBSITES: PublicVitrineDemo[] = [
  {
    id: "web-cinematic-hot-dog",
    niche: "restaurant",
    kind: "website",
    packageId: "premium",
    href: "/package-previews/premium/hot-dog/index.html",
    thumb: "/package-previews/premium/hot-dog/assets/seq/f001.jpg",
    emoji: "🌭",
    labelKey: "examples.restaurant",
    fallback: "Hot Dog / Street Food",
    blurb: "Cinematic Scroll",
    priceKind: "website",
    badge: "Cinematic",
  },
  {
    id: "web-cinematic-barbershop",
    niche: "beauty",
    kind: "website",
    packageId: "premium",
    href: "/package-previews/premium/barbershop/index.html",
    thumb: "/package-previews/premium/barbershop/assets/seq/f001.jpg",
    emoji: "💈",
    labelKey: "examples.beauty",
    fallback: "Barbershop",
    blurb: "Cinematic Scroll",
    priceKind: "website",
    badge: "Cinematic",
  },
  {
    id: "web-cinematic-brows",
    niche: "beauty",
    kind: "website",
    packageId: "premium",
    href: "/package-previews/premium/beauty-brows/index.html",
    thumb: "/package-previews/premium/beauty-brows/assets/seq/f001.jpg",
    emoji: "✨",
    labelKey: "examples.beauty",
    fallback: "Brows Studio",
    blurb: "Cinematic Scroll",
    priceKind: "website",
    badge: "Cinematic",
  },
];

export const PUBLIC_VITRINE_CINEMATIC_STORES: PublicVitrineDemo[] = [
  {
    id: "shop-cinematic-fashion",
    niche: "fashion",
    kind: "store",
    packageId: "premium",
    href: "/package-previews/premium/shop-fashion-v2/index.html",
    thumb: "/package-previews/premium/shop-fashion-v2/assets/cinematic/c001.jpg",
    emoji: "👗",
    labelKey: "examples.fashionStore",
    fallback: "Fashion Store",
    blurb: "Cinematic Shop",
    priceKind: "store",
    badge: "Cinematic",
  },
];

function withPackageBadge(
  demos: PublicVitrineDemo[],
  pkg: PublicVitrinePackage,
): PublicVitrineDemo[] {
  const badge = pkg === "premium" ? "Premium Cinematic" : "Business Cinematic";
  return demos.map((d) => ({
    ...d,
    id: d.id.replace(/-(premium|business)-/, `-${pkg}-`).replace("web-cinematic", `web-${pkg}-cinematic`).replace("shop-cinematic", `shop-${pkg}-cinematic`),
    packageId: pkg,
    badge,
  }));
}

export const PUBLIC_VITRINE_WEBSITES_BASIC = buildWebsitePackage("basic");
/** Business = newer premium-folder demos + cinematic scroll (not basic) */
export const PUBLIC_VITRINE_WEBSITES_BUSINESS = [
  ...withPackageBadge(PUBLIC_VITRINE_CINEMATIC_WEBSITES, "business"),
  ...buildWebsitePackage("business"),
];
/** Premium = cinematic first + newer premium-folder demos */
export const PUBLIC_VITRINE_WEBSITES_PREMIUM = [
  ...withPackageBadge(PUBLIC_VITRINE_CINEMATIC_WEBSITES, "premium"),
  ...buildWebsitePackage("premium"),
];

export const PUBLIC_VITRINE_STORES_BASIC = buildStorePackage("basic");
export const PUBLIC_VITRINE_STORES_BUSINESS = [
  ...withPackageBadge(PUBLIC_VITRINE_CINEMATIC_STORES, "business"),
  ...buildStorePackage("business"),
];
export const PUBLIC_VITRINE_STORES_PREMIUM = [
  ...withPackageBadge(PUBLIC_VITRINE_CINEMATIC_STORES, "premium"),
  ...buildStorePackage("premium"),
];

/** Flat lists used by packagePreviewGallery / gates */
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
    priceLabel: "199 €",
    virtusControl: false,
    includes: [
      "Fertige Website für Ihre Branche",
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
    priceLabel: "399 €",
    virtusControl: true,
    includes: [
      "Alles aus Basic",
      "Mehr Seiten / erweiterte Struktur",
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
    priceLabel: "699 €",
    virtusControl: true,
    includes: [
      "Alles aus Business",
      "Premium Design & Motion",
      "Cinematic Experience (wo verfügbar)",
      "Erweiterte Steuerung & Support-Level",
      "Virtus AI Assist im Workspace",
    ],
    controlLines: [
      "Alles aus Business-Steuerung",
      "Hero / Media / Cinematic Szenen",
      "Feinere Design- und Content-Kontrolle",
      "Restore Original / Versionen",
    ],
  },
];

export const STORE_PACKAGE_INCLUDES: PackageIncludesBlock[] = [
  {
    packageId: "basic",
    kind: "store",
    priceLabel: "Start · ab 799 €",
    virtusControl: false,
    includes: [
      "Online-Shop mit Katalog",
      "Produktseiten & Preise",
      "Warenkorb / Bestellweg (Demo/Live je nach Setup)",
      "Responsive Shop-Design",
    ],
    controlLines: ["Kein volles Virtus Shop-Admin (Änderungen über Auftrag/Support)"],
  },
  {
    packageId: "business",
    kind: "store",
    priceLabel: "Business · ab 1 499 €",
    virtusControl: true,
    includes: [
      "Alles aus Start/Basic",
      "Virtus Shop Admin",
      "Produkte · Kategorien · Bestellungen",
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
    priceLabel: "Premium · ab 2 499 €",
    virtusControl: true,
    includes: [
      "Alles aus Business",
      "Premium Shop Design & cinematic Produktpräsentation",
      "Erweiterte Steuerung & Analytics",
      "Virtus AI Assist im Shop Workspace",
    ],
    controlLines: [
      "Alles aus Business-Admin",
      "Design / Hero / Media",
      "Cinematic Produkt-Story",
      "Restore Original / Versionen",
    ],
  },
];

export const PUBLIC_VITRINE_LEGACY_BLOCKLIST = [
  "/package-previews/client-forms/",
  "/package-previews/client-forms/studio-lumia/",
] as const;

export const PUBLIC_VITRINE_THUMB_VERSION = "v17basicVsStudio";

export function isLegacyPublicPreview(href: string): boolean {
  const h = href.replace(/\\/g, "/");
  return PUBLIC_VITRINE_LEGACY_BLOCKLIST.some((p) => h.includes(p));
}

export function allPublicVitrineHrefs(): string[] {
  return PUBLIC_VITRINE_EXAMPLES.map((d) => d.href);
}

export function allPublicVitrineThumbs(): string[] {
  return PUBLIC_VITRINE_EXAMPLES.map((d) => d.thumb);
}

function nichePackageCount(demos: PublicVitrineDemo[]): number {
  return demos.filter((d) => !(d.badge || "").includes("Cinematic")).length;
}

export function assertEqualPackageExampleCounts(): boolean {
  return (
    PUBLIC_VITRINE_WEBSITES_BASIC.length === PACKAGE_EXAMPLE_COUNT &&
    PUBLIC_VITRINE_WEBSITES_BUSINESS.length === PACKAGE_EXAMPLE_COUNT &&
    nichePackageCount(PUBLIC_VITRINE_WEBSITES_PREMIUM) === PACKAGE_EXAMPLE_COUNT &&
    PUBLIC_VITRINE_STORES_BASIC.length === PACKAGE_EXAMPLE_COUNT &&
    PUBLIC_VITRINE_STORES_BUSINESS.length === PACKAGE_EXAMPLE_COUNT &&
    nichePackageCount(PUBLIC_VITRINE_STORES_PREMIUM) === PACKAGE_EXAMPLE_COUNT
  );
}
