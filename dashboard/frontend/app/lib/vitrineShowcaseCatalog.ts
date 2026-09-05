/**
 * Commercial /site showcase — maps real PUBLISHED demos + honest mockup panes.
 * Never present a website hero as a shop/bot/office visual.
 */

import {
  PUBLIC_AGENCY_PORTFOLIO,
  PUBLIC_VITRINE_STORES,
  PUBLIC_VITRINE_THUMB_VERSION,
  PUBLIC_VITRINE_WEBSITES,
} from "./publicVitrineCatalog";

const V = PUBLIC_VITRINE_THUMB_VERSION;

export type ShowcasePaneId =
  | "websites"
  | "shops"
  | "bots"
  | "office"
  | "automation";

export type GalleryItem = {
  id: string;
  title: string;
  blurb: string;
  /** Real preview image when available */
  thumb?: string;
  href?: string;
  /** Visual kind for mockup cards */
  kind?: "chat" | "doc" | "flow" | "photo";
};

function publishedWebsites() {
  return PUBLIC_VITRINE_WEBSITES.filter((d) => d.showcaseStatus === "PUBLISHED");
}

function publishedStores() {
  return PUBLIC_VITRINE_STORES.filter((d) => d.showcaseStatus === "PUBLISHED");
}

/** Hero carousel slides for websites — real demos only */
export function websiteShowcaseSlides(): GalleryItem[] {
  const portfolio = PUBLIC_AGENCY_PORTFOLIO.filter(
    (p) => p.showcaseStatus === "PUBLISHED",
  ).map((p) => ({
    id: p.id,
    title: p.title,
    blurb: p.tag,
    thumb: `${p.previewImage}?v=${V}`,
    href: p.livePreviewUrl,
    kind: "photo" as const,
  }));
  const extras = publishedWebsites()
    .filter((d) => !portfolio.some((p) => p.href === d.href))
    .slice(0, 6)
    .map((d) => ({
      id: d.id,
      title: d.fallback,
      blurb: d.blurb,
      thumb: `${d.thumb}?v=${V}`,
      href: d.href,
      kind: "photo" as const,
    }));
  return [...portfolio, ...extras].slice(0, 8);
}

export function shopShowcaseSlides(): GalleryItem[] {
  return publishedStores()
    .slice(0, 6)
    .map((d) => ({
      id: d.id,
      title: d.fallback,
      blurb: d.blurb,
      thumb: `${d.thumb}?v=${V}`,
      href: d.href,
      kind: "photo" as const,
    }));
}

/** Bot gallery — mockup kinds only (no website screenshots) */
export const BOT_GALLERY: GalleryItem[] = [
  {
    id: "bot-receptionist",
    title: "AI Receptionist",
    blurb: "Qualifies inquiries · Telegram + website chat",
    kind: "chat",
  },
  {
    id: "bot-support",
    title: "Customer Support",
    blurb: "Answers from your confirmed knowledge",
    kind: "chat",
  },
  {
    id: "bot-sales",
    title: "Sales",
    blurb: "Guides buyers to the right package",
    kind: "chat",
  },
  {
    id: "bot-booking",
    title: "Booking",
    blurb: "Collects time, place, photos for the owner",
    kind: "chat",
  },
  {
    id: "bot-faq",
    title: "FAQ",
    blurb: "Honest answers — no invented product facts",
    kind: "chat",
  },
];

export const OFFICE_GALLERY: GalleryItem[] = [
  { id: "off-pdf", title: "PDF", blurb: "Upload & analyze", kind: "doc" },
  { id: "off-docx", title: "DOCX", blurb: "Structured Word output", kind: "doc" },
  { id: "off-xlsx", title: "Excel / XLSX", blurb: "Tables & extracts", kind: "doc" },
  { id: "off-csv", title: "CSV", blurb: "Clean tabular data", kind: "doc" },
  { id: "off-ocr", title: "OCR", blurb: "Readable photos & scans", kind: "doc" },
  { id: "off-translate", title: "Translation", blurb: "Any → any target language", kind: "doc" },
  { id: "off-calc", title: "Calculations", blurb: "From your numbers only", kind: "doc" },
  { id: "off-gen", title: "Document generation", blurb: "CV · letters · drafts", kind: "doc" },
];

export const AUTOMATION_GALLERY: GalleryItem[] = [
  {
    id: "auto-lead",
    title: "Lead → qualify",
    blurb: "Inquiry captured and structured",
    kind: "flow",
  },
  {
    id: "auto-crm",
    title: "CRM task",
    blurb: "Owner gets a ready follow-up",
    kind: "flow",
  },
  {
    id: "auto-follow",
    title: "Follow-up",
    blurb: "Reminders for the owner",
    kind: "flow",
  },
  {
    id: "auto-ai",
    title: "AI employee",
    blurb: "Defined role with allowed actions",
    kind: "flow",
  },
];

export const SHOWCASE_PANES: {
  id: ShowcasePaneId;
  href: string;
  available: boolean;
  ctaHref: string;
}[] = [
  { id: "websites", href: "/site/websites", available: true, ctaHref: "/order?form=1" },
  { id: "shops", href: "/site/shops", available: true, ctaHref: "/order/shop" },
  { id: "bots", href: "/site/bots", available: true, ctaHref: "/order/bot" },
  { id: "office", href: "/office", available: true, ctaHref: "/office" },
  {
    id: "automation",
    href: "/site#b2b",
    available: true,
    ctaHref: "/order/service/business_automation?form=1",
  },
];