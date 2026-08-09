/**
 * Public /site vitrine demos — Website + AI Store by niche only.
 * No Basic/Business/Premium tier compare. No LUMIA / client-forms.
 *
 * Prices: commercialCatalog LANDING_PACKAGES_EUR (Standalone) + Store 799 €.
 */

export type PublicVitrineKind = "website" | "store";

export type PublicVitrineDemo = {
  id: string;
  kind: PublicVitrineKind;
  href: string;
  thumb: string;
  emoji: string;
  labelKey: string;
  fallback: string;
  blurb: string;
  priceKind: "website" | "store";
};

export const PUBLIC_VITRINE_WEBSITES: PublicVitrineDemo[] = [
  {
    id: "beauty",
    kind: "website",
    href: "/package-previews/sites/premium/beauty/index.html",
    thumb: "/vitrine/web-beauty.jpg",
    emoji: "💅",
    labelKey: "examples.beauty",
    fallback: "Beauty",
    blurb: "Salon, Pflege, Termin — eigene Markenatmosphäre",
    priceKind: "website",
  },
  {
    id: "cleaning",
    kind: "website",
    href: "/package-previews/sites/premium/cleaning/index.html",
    thumb: "/vitrine/web-cleaning.jpg",
    emoji: "🧹",
    labelKey: "examples.cleaning",
    fallback: "Reinigung",
    blurb: "Privat & Gewerbe — sichtbar sauber",
    priceKind: "website",
  },
  {
    id: "it",
    kind: "website",
    href: "/package-previews/sites/premium/it_support/index.html",
    thumb: "/vitrine/web-it.jpg",
    emoji: "💻",
    labelKey: "examples.it",
    fallback: "IT Support",
    blurb: "Diagnose, Reparatur, Datenrettung",
    priceKind: "website",
  },
  {
    id: "dental",
    kind: "website",
    href: "/package-previews/sites/premium/dental/index.html",
    thumb: "/vitrine/web-dental.jpg",
    emoji: "🦷",
    labelKey: "examples.dental",
    fallback: "Zahnarzt",
    blurb: "Praxis, Vorsorge, Termin",
    priceKind: "website",
  },
  {
    id: "restaurant",
    kind: "website",
    href: "/package-previews/sites/premium/restaurant/index.html",
    thumb: "/vitrine/web-restaurant.jpg",
    emoji: "🍽",
    labelKey: "examples.restaurant",
    fallback: "Restaurant",
    blurb: "Menü, Reservierung, Atmosphäre",
    priceKind: "website",
  },
  {
    id: "handwerk",
    kind: "website",
    href: "/package-previews/sites/premium/handwerk/index.html",
    thumb: "/vitrine/web-handwerk.jpg",
    emoji: "🔨",
    labelKey: "examples.handwerk",
    fallback: "Handwerk",
    blurb: "Meister vor Ort — Projekte & Festpreis",
    priceKind: "website",
  },
  {
    id: "law",
    kind: "website",
    href: "/package-previews/sites/premium/law/index.html",
    thumb: "/vitrine/web-law.jpg",
    emoji: "⚖️",
    labelKey: "examples.law",
    fallback: "Rechtsanwalt",
    blurb: "Bereiche, Team, Erstgespräch",
    priceKind: "website",
  },
  {
    id: "auto",
    kind: "website",
    href: "/package-previews/sites/premium/auto/index.html",
    thumb: "/vitrine/web-auto.jpg",
    emoji: "🔧",
    labelKey: "examples.auto",
    fallback: "Autowerkstatt",
    blurb: "Diagnose, Inspektion, Reparatur",
    priceKind: "website",
  },
];

export const PUBLIC_VITRINE_STORES: PublicVitrineDemo[] = [
  {
    id: "beauty-store",
    kind: "store",
    href: "/package-previews/stores/premium/beauty/catalog.html",
    thumb: "/vitrine/store-beauty.jpg",
    emoji: "🧴",
    labelKey: "examples.beautyStore",
    fallback: "Beauty Store",
    blurb: "Pflegeprodukte, Bundles, Checkout",
    priceKind: "store",
  },
  {
    id: "cleaning-store",
    kind: "store",
    href: "/package-previews/stores/premium/cleaning_shop/catalog.html",
    thumb: "/vitrine/store-cleaning.jpg",
    emoji: "🧼",
    labelKey: "examples.cleaningStore",
    fallback: "Cleaning Store",
    blurb: "Reinigungsmittel & Bundles",
    priceKind: "store",
  },
  {
    id: "electronics-store",
    kind: "store",
    href: "/package-previews/stores/premium/electronics/catalog.html",
    thumb: "/vitrine/store-electronics.jpg",
    emoji: "🔌",
    labelKey: "examples.electronicsStore",
    fallback: "Electronics Store",
    blurb: "Geräte, Zubehör, Specs",
    priceKind: "store",
  },
  {
    id: "food-store",
    kind: "store",
    href: "/package-previews/stores/premium/food/catalog.html",
    thumb: "/vitrine/store-food.jpg",
    emoji: "🛒",
    labelKey: "examples.foodStore",
    fallback: "Food Store",
    blurb: "Feinkost, Sets, Lieferung",
    priceKind: "store",
  },
  {
    id: "furniture-store",
    kind: "store",
    href: "/package-previews/stores/premium/furniture/catalog.html",
    thumb: "/vitrine/store-furniture.jpg",
    emoji: "🪑",
    labelKey: "examples.furnitureStore",
    fallback: "Furniture Store",
    blurb: "Möbel, Räume, Checkout",
    priceKind: "store",
  },
  {
    id: "fashion-store",
    kind: "store",
    href: "/package-previews/stores/premium/fashion/catalog.html",
    thumb: "/vitrine/store-fashion.jpg",
    emoji: "👗",
    labelKey: "examples.fashionStore",
    fallback: "Fashion Store",
    blurb: "Looks, Kollektionen, Warenkorb",
    priceKind: "store",
  },
];

/** Flat list for gates / legacy imports. */
export const PUBLIC_VITRINE_EXAMPLES: PublicVitrineDemo[] = [
  ...PUBLIC_VITRINE_WEBSITES,
  ...PUBLIC_VITRINE_STORES,
];

export const PUBLIC_VITRINE_LEGACY_BLOCKLIST = [
  "/package-previews/client-forms/",
  "/package-previews/client-forms/studio-lumia/",
  "/package-previews/sites/basic/",
  "/package-previews/sites/business/",
] as const;

/** Cache-bust query for public thumbs after media rebuilds. */
export const PUBLIC_VITRINE_THUMB_VERSION = "v13plates";

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
