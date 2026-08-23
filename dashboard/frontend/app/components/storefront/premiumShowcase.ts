/** Premium Showcase — Website ≠ Online-Shop (two products). */

export type PremiumShowcaseKind = "website" | "shop";

export type PremiumShowcaseCard = {
  id: string;
  niche: string;
  kind: PremiumShowcaseKind;
  label: string;
  format: string;
  storyLine: string;
  href: string;
  status: "live_showcase" | "planned";
  productCountLabel?: string;
  features?: string[];
};

/** Live Premium Websites — cinematic ACTION→TRANSFORM→RESULT (do not break). */
export const PREMIUM_WEBSITES_LIVE: PremiumShowcaseCard[] = [
  {
    id: "hot_dog",
    niche: "Hot Dog / Street Food",
    kind: "website",
    label: "Hot Dog / Street Food",
    format: "Cinematic Website",
    storyLine: "Grill → Goldbraun → Fertig → Jetzt probieren",
    href: "/package-previews/premium/hot-dog/index.html",
    status: "live_showcase",
  },
  {
    id: "barbershop",
    niche: "Barbershop",
    kind: "website",
    label: "Barbershop",
    format: "Cinematic Website",
    storyLine: "Haircut → Styling → Final Look",
    href: "/package-previews/premium/barbershop/index.html",
    status: "live_showcase",
  },
  {
    id: "beauty_brows",
    niche: "Brows",
    kind: "website",
    label: "Brows",
    format: "Cinematic Website",
    storyLine: "Mapping → Technik → Dein Look",
    href: "/package-previews/premium/beauty-brows/index.html",
    status: "live_showcase",
  },
];

/** Expanded website niches on vitrine (planned until cinematic demo is ready). */
export const PREMIUM_WEBSITES_PLANNED: PremiumShowcaseCard[] = [
  { id: "beauty_studio", niche: "Beauty Studio", kind: "website", label: "Beauty Studio", format: "Cinematic Website", storyLine: "Prep → Behandlung → Glow → Termin", href: "#", status: "planned" },
  { id: "beauty_lashes", niche: "Eyelashes", kind: "website", label: "Eyelashes", format: "Cinematic Website", storyLine: "Before → Application → Finish → Termin", href: "#", status: "planned" },
  { id: "nails", niche: "Nails", kind: "website", label: "Nails", format: "Cinematic Website", storyLine: "Prep → Form → Farbe → Finish", href: "#", status: "planned" },
  { id: "hair_salon", niche: "Hair Salon", kind: "website", label: "Hair Salon", format: "Cinematic Website", storyLine: "Wash → Cut → Color → Style", href: "#", status: "planned" },
  { id: "makeup", niche: "Makeup", kind: "website", label: "Makeup", format: "Cinematic Website", storyLine: "Base → Eyes → Lips → Look", href: "#", status: "planned" },
  { id: "restaurant", niche: "Restaurant", kind: "website", label: "Restaurant", format: "Cinematic Website", storyLine: "Küche → Anrichten → Teller → Reservieren", href: "#", status: "planned" },
  { id: "cafe", niche: "Café", kind: "website", label: "Café", format: "Cinematic Website", storyLine: "Bohnen → Brühen → Tasse → Besuch", href: "#", status: "planned" },
  { id: "bakery", niche: "Bakery", kind: "website", label: "Bakery", format: "Cinematic Website", storyLine: "Teig → Ofen → Kruste → Frisch", href: "#", status: "planned" },
  { id: "pizza", niche: "Pizza", kind: "website", label: "Pizza", format: "Cinematic Website", storyLine: "Teig → Belag → Ofen → Heiß", href: "#", status: "planned" },
  { id: "burger", niche: "Burger", kind: "website", label: "Burger", format: "Cinematic Website", storyLine: "Patty → Grill → Stack → Bestellen", href: "#", status: "planned" },
  { id: "catering", niche: "Catering", kind: "website", label: "Catering", format: "Cinematic Website", storyLine: "Menü → Prep → Service → Event", href: "#", status: "planned" },
  { id: "dental", niche: "Dental", kind: "website", label: "Dental", format: "Cinematic Website", storyLine: "Beratung → Behandlung → Smile → Termin", href: "#", status: "planned" },
  { id: "law", niche: "Law", kind: "website", label: "Law", format: "Cinematic Website", storyLine: "Klarheit → Beratung → Vertrauen → Kontakt", href: "#", status: "planned" },
  { id: "consulting", niche: "Consulting", kind: "website", label: "Consulting", format: "Cinematic Website", storyLine: "Analyse → Plan → Ergebnis → Gespräch", href: "#", status: "planned" },
  { id: "it", niche: "IT", kind: "website", label: "IT", format: "Cinematic Website", storyLine: "Problem → Lösung → System → Kontakt", href: "#", status: "planned" },
  { id: "marketing", niche: "Marketing", kind: "website", label: "Marketing", format: "Cinematic Website", storyLine: "Brief → Kampagne → Reach → Kontakt", href: "#", status: "planned" },
  { id: "real_estate", niche: "Real Estate", kind: "website", label: "Real Estate", format: "Cinematic Website", storyLine: "Objekt → Rundgang → Detail → Besichtigung", href: "#", status: "planned" },
  { id: "photography", niche: "Photography", kind: "website", label: "Photography", format: "Cinematic Website", storyLine: "Setup → Shoot → Edit → Anfrage", href: "#", status: "planned" },
  { id: "auto", niche: "Auto", kind: "website", label: "Auto", format: "Cinematic Website", storyLine: "Diagnose → Reparatur → Finish → Termin", href: "#", status: "planned" },
  { id: "handwerk", niche: "Handwerk", kind: "website", label: "Handwerk", format: "Cinematic Website", storyLine: "Material → Handwerk → Ergebnis → Angebot", href: "#", status: "planned" },
  { id: "construction", niche: "Construction", kind: "website", label: "Construction", format: "Cinematic Website", storyLine: "Plan → Bau → Detail → Angebot", href: "#", status: "planned" },
  { id: "cleaning", niche: "Cleaning", kind: "website", label: "Cleaning", format: "Cinematic Website", storyLine: "Vorher → Arbeit → Nachher → Anfrage", href: "#", status: "planned" },
  { id: "landscaping", niche: "Landscaping", kind: "website", label: "Landscaping", format: "Cinematic Website", storyLine: "Garten → Arbeit → Grün → Anfrage", href: "#", status: "planned" },
  { id: "fitness", niche: "Fitness", kind: "website", label: "Fitness", format: "Cinematic Website", storyLine: "Prep → Training → Effort → Membership", href: "#", status: "planned" },
  { id: "personal_trainer", niche: "Personal Trainer", kind: "website", label: "Personal Trainer", format: "Cinematic Website", storyLine: "Goal → Session → Progress → Start", href: "#", status: "planned" },
  { id: "hotel", niche: "Hotel", kind: "website", label: "Hotel", format: "Cinematic Website", storyLine: "Ankunft → Suite → Detail → Buchen", href: "#", status: "planned" },
  { id: "apartment", niche: "Apartment", kind: "website", label: "Apartment", format: "Cinematic Website", storyLine: "Eingang → Raum → Detail → Buchen", href: "#", status: "planned" },
  { id: "spa", niche: "Spa", kind: "website", label: "Spa", format: "Cinematic Website", storyLine: "Ruhe → Ritual → Erholung → Termin", href: "#", status: "planned" },
  { id: "event_venue", niche: "Event Venue", kind: "website", label: "Event Venue", format: "Cinematic Website", storyLine: "Raum → Setup → Moment → Anfrage", href: "#", status: "planned" },
];

/** Live Premium Online-Shops — commerce product (not website). */
export const PREMIUM_SHOPS_LIVE: PremiumShowcaseCard[] = [
  {
    id: "fashion_v2",
    niche: "Fashion",
    kind: "shop",
    label: "Fashion Store",
    format: "Premium Online-Shop",
    storyLine: "Desire → Product → Detail → Cart",
    href: "/package-previews/premium/shop-fashion-v2/index.html",
    status: "live_showcase",
    productCountLabel: "24+ products",
    features: ["Cart", "Account", "Orders"],
  },
];

export const PREMIUM_SHOPS_PLANNED: PremiumShowcaseCard[] = [
  { id: "electronics_v2", niche: "Electronics", kind: "shop", label: "Electronics", format: "Premium Online-Shop", storyLine: "Reveal → Specs → Kaufen", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "food_shop", niche: "Food", kind: "shop", label: "Food Store", format: "Premium Online-Shop", storyLine: "Menu → Price → Bestellen", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "beauty_products", niche: "Beauty Products", kind: "shop", label: "Beauty Products", format: "Premium Online-Shop", storyLine: "Texture → Product → Cart", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "cosmetics", niche: "Cosmetics", kind: "shop", label: "Cosmetics", format: "Premium Online-Shop", storyLine: "Swatch → Apply → Shop", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "furniture", niche: "Furniture", kind: "shop", label: "Furniture", format: "Premium Online-Shop", storyLine: "Material → Room → Shop", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "watches", niche: "Watches", kind: "shop", label: "Watches", format: "Premium Online-Shop", storyLine: "Macro → Hero → Kaufen", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "jewelry", niche: "Jewelry", kind: "shop", label: "Jewelry", format: "Premium Online-Shop", storyLine: "Sparkle → Piece → Cart", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "sports", niche: "Sports", kind: "shop", label: "Sports", format: "Premium Online-Shop", storyLine: "Motion → Gear → Cart", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "home_living", niche: "Home & Living", kind: "shop", label: "Home & Living", format: "Premium Online-Shop", storyLine: "Raum → Produkt → Shop", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "shoes", niche: "Shoes", kind: "shop", label: "Shoes", format: "Premium Online-Shop", storyLine: "Form → Detail → Cart", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
  { id: "accessories", niche: "Accessories", kind: "shop", label: "Accessories", format: "Premium Online-Shop", storyLine: "Detail → Style → Cart", href: "#", status: "planned", productCountLabel: "20+ products", features: ["Cart", "Account", "Orders"] },
];

/** @deprecated use PREMIUM_WEBSITES_LIVE / PREMIUM_SHOPS_LIVE */
export const PREMIUM_SHOWCASE_TIER1: PremiumShowcaseCard[] = [
  ...PREMIUM_WEBSITES_LIVE,
  ...PREMIUM_SHOPS_LIVE,
];
