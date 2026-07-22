/**
 * UI labels for Business Knowledge categories — mirrors portal ALLOWED list.
 * Not a domain model; presentation only.
 */

export const KNOWLEDGE_CATEGORIES = [
  "company",
  "services",
  "products",
  "pricing",
  "working_hours",
  "faq",
  "policies",
  "contacts",
] as const;

export type KnowledgeCategoryId = (typeof KNOWLEDGE_CATEGORIES)[number];

export const KNOWLEDGE_CATEGORY_META: Record<
  KnowledgeCategoryId,
  { label: string; hint: string; titlePlaceholder: string; contentPlaceholder: string }
> = {
  company: {
    label: "Company",
    hint: "Who you are and what you do",
    titlePlaceholder: "About us",
    contentPlaceholder: "Family dental clinic in Berlin…",
  },
  services: {
    label: "Services",
    hint: "What you offer",
    titlePlaceholder: "Core services",
    contentPlaceholder: "Cleaning, whitening, implants…",
  },
  products: {
    label: "Products",
    hint: "Goods or packages",
    titlePlaceholder: "Product line",
    contentPlaceholder: "Care kits, gift cards…",
  },
  pricing: {
    label: "Pricing",
    hint: "Prices and packages",
    titlePlaceholder: "Price list",
    contentPlaceholder: "Consultation from €50…",
  },
  working_hours: {
    label: "Working hours",
    hint: "When you are open",
    titlePlaceholder: "Opening hours",
    contentPlaceholder: "Mon–Fri 09:00–19:00",
  },
  faq: {
    label: "FAQ",
    hint: "Common customer questions",
    titlePlaceholder: "Do you accept insurance?",
    contentPlaceholder: "Yes, we work with…",
  },
  policies: {
    label: "Policies",
    hint: "Rules and guarantees",
    titlePlaceholder: "Cancellation policy",
    contentPlaceholder: "Free cancel 24h before…",
  },
  contacts: {
    label: "Contacts",
    hint: "How to reach you",
    titlePlaceholder: "Main contact",
    contentPlaceholder: "Phone, address, email…",
  },
};
