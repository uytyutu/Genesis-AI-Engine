/**
 * Service storefront specs — cards + intake forms (form → confirm → pay).
 * Keep IDs in sync with commercial_catalog_g23 / sales_order_service.
 */

export type ServiceFieldId =
  | "email"
  | "business_name"
  | "website_url"
  | "city"
  | "phone"
  | "whatsapp"
  | "goal"
  | "notes"
  | "access_notes"
  | "gbp_name"
  | "gbp_category"
  | "hosting_from"
  | "hosting_to";

export type ServiceField = {
  id: ServiceFieldId;
  label: string;
  placeholder?: string;
  required?: boolean;
  multiline?: boolean;
  type?: "email" | "url" | "tel" | "text";
};

export type ServiceSpec = {
  id: string;
  name: string;
  price_label: string;
  blurb: string;
  mark: string;
  accent: string;
  availability: "available" | "coming_soon";
  href: string;
  fields: ServiceField[];
  deliveryNote: string;
  /** Trust block on cards + confirmation screen */
  includes: string[];
  stages: string[];
  timeline: string;
  afterPay: string[];
  support: string;
};

const contactFields: ServiceField[] = [
  {
    id: "email",
    label: "Email",
    type: "email",
    required: true,
    placeholder: "you@company.com",
  },
  {
    id: "business_name",
    label: "Company / brand",
    required: true,
    placeholder: "Your business name",
  },
  {
    id: "phone",
    label: "Phone",
    type: "tel",
    placeholder: "+49 …",
  },
];

export const SERVICE_SPECS: ServiceSpec[] = [
  {
    id: "landing_website",
    name: "Create a website",
    price_label: "350–1200 €",
    blurb: "Landing packages — Basic, Business, Premium.",
    mark: "W",
    accent: "border-emerald-400/35 bg-emerald-500/[0.08]",
    availability: "available",
    href: "/order",
    fields: [],
    deliveryNote: "Full order form with packages and materials.",
    includes: ["Mobile landing", "Impressum / Datenschutz ready", "Files you own"],
    stages: ["Brief", "Build", "Review", "Handover"],
    timeline: "typically 3–10 days after brief",
    afterPay: ["Project opens in cabinet", "Vector follows progress"],
    support: "Vector + cabinet status",
  },
  {
    id: "ai_business_bot",
    name: "AI Digital Employee",
    price_label: "from 499 € + monthly",
    blurb:
      "AI Sales Assistant for your company — answers customers on Website Chat, Telegram, WhatsApp, Instagram, Messenger.",
    mark: "B",
    accent: "border-sky-400/35 bg-sky-500/[0.08]",
    availability: "available",
    href: "/order/bot",
    fields: [],
    deliveryNote: "Wizard: package → account → company → channels → pay.",
    includes: [
      "One AI employee for your brand",
      "Channels you choose",
      "Workspace after payment",
    ],
    stages: ["Package", "Account", "Company & AI", "Channels", "Pay", "Connect"],
    timeline: "connect channels right after payment",
    afterPay: ["Open Workspace", "Connect Telegram / Meta", "Go live"],
    support: "Cabinet + Vector setup help",
  },
  {
    id: "ai_website_analysis",
    name: "Analyze my website",
    price_label: "149 €",
    blurb: "AI report + priorities — no website purchase required.",
    mark: "A",
    accent: "border-violet-400/35 bg-violet-500/[0.08]",
    availability: "available",
    href: "/order/service/ai_website_analysis",
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Website URL",
        type: "url",
        required: true,
        placeholder: "https://…",
      },
      {
        id: "goal",
        label: "What should we focus on?",
        required: true,
        multiline: true,
        placeholder: "Speed, mobile, SEO, forms…",
      },
    ],
    deliveryNote: "Written report with priorities in your cabinet.",
    includes: ["HTTPS / mobile / speed checks", "Priority list", "Repair vs new-site advice"],
    stages: ["Form", "Payment", "Report in cabinet"],
    timeline: "report within 1–3 business days",
    afterPay: ["Case opens", "You receive the report", "Optional repair offer"],
    support: "Cabinet + Vector questions",
  },
  {
    id: "website_repair",
    name: "Website Repair",
    price_label: "from 199 €",
    blurb: "Emergency Website Recovery — fix an existing site without buying a new Landing.",
    mark: "R",
    accent: "border-amber-400/35 bg-amber-500/[0.08]",
    availability: "available",
    href: "/order/service/website_repair",
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Website URL",
        type: "url",
        required: true,
        placeholder: "https://…",
      },
      {
        id: "goal",
        label: "What must be fixed?",
        required: true,
        multiline: true,
        placeholder: "Broken mobile menu, slow images, contact form…",
      },
      {
        id: "access_notes",
        label: "Access notes (optional)",
        multiline: true,
        placeholder: "Hosting / CMS login will be shared after payment",
      },
    ],
    deliveryNote: "Operator-led repair after payment — status in your cabinet.",
    includes: ["Agreed repair scope", "Before/after notes", "Cabinet tracking"],
    stages: ["Form", "Payment", "Access", "Repair", "Handover"],
    timeline: "typically 2–5 business days after access",
    afterPay: ["We request access securely", "Work starts", "You approve result"],
    support: "Vector + cabinet status",
  },
  {
    id: "seo_audit",
    name: "SEO Audit",
    price_label: "249 €",
    blurb: "Technical + local SEO plan.",
    mark: "S",
    accent: "border-white/15 bg-white/[0.04]",
    availability: "coming_soon",
    href: "/order/service/seo_audit",
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Website URL",
        type: "url",
        required: true,
        placeholder: "https://…",
      },
      {
        id: "goal",
        label: "SEO goal",
        required: true,
        multiline: true,
        placeholder: "Local Google ranking, keywords, competitors…",
      },
    ],
    deliveryNote: "Interest form open — checkout when delivery is live.",
    includes: ["Technical SEO check", "Meta / structure", "Action plan"],
    stages: ["Interest", "Brief", "Audit delivery"],
    timeline: "2–4 days when live",
    afterPay: ["Opens when service is live"],
    support: "Vector waitlist",
  },
  {
    id: "speed_optimization",
    name: "Speed Optimization",
    price_label: "199 €",
    blurb: "Load-time improvements for your site.",
    mark: "V",
    accent: "border-white/15 bg-white/[0.04]",
    availability: "coming_soon",
    href: "/order/service/speed_optimization",
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Website URL",
        type: "url",
        required: true,
      },
      {
        id: "goal",
        label: "What feels slow?",
        required: true,
        multiline: true,
        placeholder: "Mobile, images, first paint…",
      },
    ],
    deliveryNote: "Interest form open — checkout when delivery is live.",
    includes: ["Before/after metrics", "Image & cache focus", "Residual list"],
    stages: ["Interest", "Measure", "Optimize"],
    timeline: "2–5 days when live",
    afterPay: ["Opens when service is live"],
    support: "Vector waitlist",
  },
  {
    id: "security_check",
    name: "Security Check",
    price_label: "299 €",
    blurb: "HTTPS, forms, vulnerability review.",
    mark: "C",
    accent: "border-white/15 bg-white/[0.04]",
    availability: "coming_soon",
    href: "/order/service/security_check",
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Website URL",
        type: "url",
        required: true,
      },
      {
        id: "goal",
        label: "Concerns",
        required: true,
        multiline: true,
        placeholder: "Forms, login, HTTPS, malware…",
      },
    ],
    deliveryNote: "Interest form open — checkout when delivery is live.",
    includes: ["HTTPS & forms review", "Priority report", "No fake pen-test claims"],
    stages: ["Interest", "Scan", "Report"],
    timeline: "1–3 days when live",
    afterPay: ["Opens when service is live"],
    support: "Vector waitlist",
  },
  {
    id: "google_business_setup",
    name: "Google Business Profile",
    price_label: "149 €",
    blurb: "Local discovery — profile setup for your company.",
    mark: "G",
    accent: "border-white/15 bg-white/[0.04]",
    availability: "coming_soon",
    href: "/order/service/google_business_setup",
    fields: [
      ...contactFields,
      {
        id: "gbp_name",
        label: "Business name on Google",
        required: true,
      },
      {
        id: "city",
        label: "City / area",
        required: true,
      },
      {
        id: "gbp_category",
        label: "Main category",
        required: true,
        placeholder: "e.g. Auto repair shop",
      },
      {
        id: "website_url",
        label: "Website (if any)",
        type: "url",
      },
      {
        id: "notes",
        label: "Hours / photos / special notes",
        multiline: true,
      },
    ],
    deliveryNote: "Form ready — checkout opens when delivery is live.",
    includes: ["Profile / categories", "Hours & contacts", "Owner checklist"],
    stages: ["Form", "Setup", "Handover"],
    timeline: "3–7 days when live",
    afterPay: ["Opens when service is live"],
    support: "Vector waitlist",
  },
  {
    id: "website_migration",
    name: "Website Migration",
    price_label: "from 299 €",
    blurb: "Move your site to new hosting.",
    mark: "M",
    accent: "border-white/15 bg-white/[0.04]",
    availability: "coming_soon",
    href: "/order/service/website_migration",
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Current website URL",
        type: "url",
        required: true,
      },
      {
        id: "hosting_from",
        label: "Current hosting",
        required: true,
        placeholder: "e.g. Wix, WordPress.com, IONOS…",
      },
      {
        id: "hosting_to",
        label: "Target hosting (if known)",
        placeholder: "Leave blank if we should advise",
      },
      {
        id: "goal",
        label: "Why migrate?",
        required: true,
        multiline: true,
      },
    ],
    deliveryNote: "Interest form open — checkout when delivery is live.",
    includes: ["Migration plan", "Cutover check", "Post-move report"],
    stages: ["Interest", "Plan", "Move", "Verify"],
    timeline: "3–10 days when live",
    afterPay: ["Opens when service is live"],
    support: "Vector waitlist",
  },
];

export function getServiceSpec(id: string): ServiceSpec | undefined {
  return SERVICE_SPECS.find((s) => s.id === id);
}

export const HUB_PRIMARY_SERVICE_IDS = [
  "landing_website",
  "ai_business_bot",
  "ai_website_analysis",
  "website_repair",
] as const;

export const HUB_MORE_SERVICE_IDS = [
  "seo_audit",
  "speed_optimization",
  "security_check",
  "google_business_setup",
  "website_migration",
] as const;
