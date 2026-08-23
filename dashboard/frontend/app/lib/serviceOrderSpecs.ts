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
  | "hosting_to"
  | "store_name";

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
  includes: string[];
  highlights?: string[];
  stages: string[];
  timeline: string;
  afterPay: string[];
  support: string;
  billing?: "one_time" | "monthly";
  /** Website Services agency section on /site */
  agencySection?: boolean;
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

const urlGoal = (
  goalLabel: string,
  goalPlaceholder: string,
): ServiceField[] => [
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
    label: goalLabel,
    required: true,
    multiline: true,
    placeholder: goalPlaceholder,
  },
];

export const SERVICE_SPECS: ServiceSpec[] = [
  {
    id: "landing_website",
    name: "Business Website",
    price_label: "199–699 €",
    blurb:
      "Start with a professional website — Basic 299 € · Business 599 € · Premium 999 €.",
    mark: "W",
    accent: "border-emerald-400/35 bg-emerald-500/[0.08]",
    availability: "available",
    href: "/order?form=1",
    fields: [],
    deliveryNote: "Full order form with packages and materials.",
    includes: [
      "Modern responsive website",
      "Impressum & Datenschutz",
      "Admin Dashboard from Business",
    ],
    stages: ["Brief", "Build", "Review", "Handover"],
    timeline: "typically 3–10 days after brief",
    afterPay: ["Project opens in cabinet", "Vector follows progress"],
    support: "Vector + cabinet status",
  },
  {
    id: "ai_business_bot",
    name: "AI Business Assistant",
    price_label: "from 499 € + monthly",
    blurb:
      "Digital employee for your company — live on Telegram today; more channels coming soon.",
    mark: "B",
    accent: "border-sky-400/35 bg-sky-500/[0.08]",
    availability: "available",
    href: "/order/bot",
    fields: [],
    deliveryNote: "Wizard: package → account → company → Telegram → pay → connect token.",
    highlights: [
      "Answers customers 24/7 on Telegram",
      "Captures leads automatically",
      "Telegram live after pay · Website Chat live · WhatsApp / Instagram — coming soon",
    ],
    includes: [
      "One AI employee for your brand",
      "Telegram live after you connect the token",
      "Workspace after payment",
    ],
    stages: ["Package", "Account", "Company & AI", "Channels", "Pay", "Connect"],
    timeline: "connect Telegram right after payment",
    afterPay: ["Open Workspace", "Connect Telegram token", "Go live"],
    support: "Cabinet + Vector setup help",
  },
  {
    id: "website_check",
    name: "Free website check",
    price_label: "Free",
    blurb:
      "See what to improve — then repair or a new site. No payment for this check.",
    mark: "A",
    accent: "border-violet-400/35 bg-violet-500/[0.08]",
    availability: "available",
    href: "/site?service=analysis",
    fields: [],
    deliveryNote: "Opens the free checker on the storefront.",
    includes: [
      "HTTPS / mobile / speed signals",
      "Clear next step",
      "Optional repair or new site",
    ],
    stages: ["URL", "Report", "Next step"],
    timeline: "results in about a minute",
    afterPay: ["Not a paid product — no checkout"],
    support: "Vector can explain the report",
  },
  {
    id: "website_repair",
    name: "Website Repair",
    price_label: "from 199 €",
    blurb: "Fix an existing site without a full rebuild — 2–5 days.",
    mark: "R",
    accent: "border-amber-400/35 bg-amber-500/[0.08]",
    availability: "available",
    href: "/order/service/website_repair",
    agencySection: true,
    fields: [
      ...urlGoal(
        "What must be fixed?",
        "Broken mobile menu, slow images, contact form…",
      ),
      {
        id: "access_notes",
        label: "Access notes (optional)",
        multiline: true,
        placeholder: "Hosting / CMS login will be shared after payment",
      },
    ],
    deliveryNote: "Operator-led repair after payment — status in your cabinet.",
    includes: [
      "Bug fixes",
      "WhatsApp button",
      "Google Maps",
      "Contact forms",
      "Basic SEO",
      "Open Graph",
    ],
    stages: ["Form", "Payment", "Access", "Repair", "Handover"],
    timeline: "2–5 days",
    afterPay: ["We request access securely", "Work starts", "You approve result"],
    support: "Vector + cabinet status",
  },
  {
    id: "ai_website_analysis",
    name: "AI Website Analysis",
    price_label: "149 €",
    blurb: "Detailed AI audit with PDF-ready report and improvement plan — 1–3 days.",
    mark: "A+",
    accent: "border-violet-400/35 bg-violet-500/[0.08]",
    availability: "available",
    href: "/order/service/ai_website_analysis",
    agencySection: true,
    fields: urlGoal("What should we focus on?", "Speed, mobile, SEO, forms…"),
    deliveryNote: "Written report with priorities in your cabinet.",
    includes: [
      "HTTPS",
      "Mobile adaptation",
      "SEO analysis",
      "Open Graph check",
      "Schema.org check",
      "PDF report",
      "Improvement plan",
    ],
    stages: ["Form", "Payment", "Report in cabinet"],
    timeline: "1–3 days",
    afterPay: ["Case opens", "You receive the report", "Optional repair offer"],
    support: "Cabinet + Vector questions",
  },
  {
    id: "seo_audit",
    name: "SEO Audit",
    price_label: "249 €",
    blurb: "Technical search-engine optimization analysis — 2–4 days.",
    mark: "S",
    accent: "border-emerald-400/30 bg-emerald-500/[0.06]",
    availability: "available",
    href: "/order/service/seo_audit",
    agencySection: true,
    fields: urlGoal("SEO goal", "Local Google ranking, keywords, competitors…"),
    deliveryNote: "Technical SEO report in your cabinet after payment.",
    includes: [
      "Title",
      "Description",
      "H1–H6",
      "robots.txt",
      "sitemap.xml",
      "Schema",
      "Core Web Vitals",
      "Fix plan",
    ],
    stages: ["Form", "Payment", "Audit delivery"],
    timeline: "2–4 days",
    afterPay: ["Project in cabinet", "Report when ready", "Download online"],
    support: "Cabinet + Vector",
  },
  {
    id: "google_business_setup",
    name: "Google Business Profile",
    price_label: "149 €",
    blurb: "Company Google profile setup — 3–7 days.",
    mark: "G",
    accent: "border-sky-400/30 bg-sky-500/[0.06]",
    availability: "available",
    href: "/order/service/google_business_setup",
    agencySection: true,
    fields: [
      ...contactFields,
      { id: "gbp_name", label: "Business name on Google", required: true },
      { id: "city", label: "City / area", required: true },
      {
        id: "gbp_category",
        label: "Main category",
        required: true,
        placeholder: "e.g. Auto repair shop",
      },
      { id: "website_url", label: "Website (if any)", type: "url" },
      {
        id: "notes",
        label: "Hours / photos / special notes",
        multiline: true,
      },
    ],
    deliveryNote: "Profile setup after payment — status in cabinet.",
    includes: [
      "Profile check",
      "Categories",
      "Opening hours",
      "Photos",
      "Links",
      "Growth plan",
    ],
    stages: ["Form", "Payment", "Setup", "Handover"],
    timeline: "3–7 days",
    afterPay: ["Project in cabinet", "Checklist when ready"],
    support: "Cabinet + Vector",
  },
  {
    id: "website_migration",
    name: "Website Migration",
    price_label: "from 299 €",
    blurb: "Move your site to a modern platform — 3–10 days.",
    mark: "M",
    accent: "border-amber-400/30 bg-amber-500/[0.06]",
    availability: "available",
    href: "/order/service/website_migration",
    agencySection: true,
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
    deliveryNote: "Migration plan and cutover after payment.",
    includes: [
      "Content migration",
      "New design",
      "Domain move help",
      "Launch support",
    ],
    stages: ["Form", "Payment", "Plan", "Move", "Verify"],
    timeline: "3–10 days",
    afterPay: ["Project in cabinet", "Cutover checklist"],
    support: "Cabinet + Vector",
  },
  {
    id: "speed_optimization",
    name: "Speed Optimization",
    price_label: "199 €",
    blurb: "Faster load times — Core Web Vitals focus — 2–5 days.",
    mark: "V",
    accent: "border-cyan-400/30 bg-cyan-500/[0.06]",
    availability: "available",
    href: "/order/service/speed_optimization",
    agencySection: true,
    fields: urlGoal("What feels slow?", "Mobile, images, first paint…"),
    deliveryNote: "Optimization work after payment — metrics in cabinet.",
    includes: [
      "Core Web Vitals",
      "Image optimization",
      "CSS / JS",
      "Caching",
      "Lazy Loading",
    ],
    stages: ["Form", "Payment", "Measure", "Optimize"],
    timeline: "2–5 days",
    afterPay: ["Project in cabinet", "Before/after notes"],
    support: "Cabinet + Vector",
  },
  {
    id: "reputation_audit",
    name: "Reputation Audit",
    price_label: "149 €",
    blurb: "Online presence and reviews analysis — 1–2 days.",
    mark: "★",
    accent: "border-yellow-400/30 bg-yellow-500/[0.06]",
    availability: "available",
    href: "/order/service/reputation_audit",
    agencySection: true,
    fields: [
      ...contactFields,
      { id: "city", label: "City / region", required: true },
      {
        id: "website_url",
        label: "Website (if any)",
        type: "url",
      },
      {
        id: "goal",
        label: "What should we check?",
        required: true,
        multiline: true,
        placeholder: "Reviews, Maps, competitors…",
      },
    ],
    deliveryNote: "Reputation report in your cabinet.",
    includes: [
      "Google Reviews",
      "Maps",
      "Mentions",
      "Recommendations",
    ],
    stages: ["Form", "Payment", "Audit"],
    timeline: "1–2 days",
    afterPay: ["Project in cabinet", "Report when ready"],
    support: "Cabinet + Vector",
  },
  {
    id: "security_check",
    name: "Security Check",
    price_label: "299 €",
    blurb: "Practical security audit for small business — 1–3 days.",
    mark: "C",
    accent: "border-rose-400/30 bg-rose-500/[0.06]",
    availability: "available",
    href: "/order/service/security_check",
    agencySection: true,
    fields: urlGoal("Concerns", "Forms, login, HTTPS, malware…"),
    deliveryNote: "Security findings in your cabinet after payment.",
    includes: [
      "HTTPS",
      "SSL",
      "Security headers",
      "Forms review",
      "Main risks",
      "Remediation plan",
    ],
    stages: ["Form", "Payment", "Scan", "Report"],
    timeline: "1–3 days",
    afterPay: ["Project in cabinet", "Report when ready"],
    support: "Cabinet + Vector",
  },
  {
    id: "ecommerce_shop",
    name: "AI Store Basic / Start",
    price_label: "799 €",
    blurb:
      "Own shop after purchase — catalog, cart, Shop Admin, German legal pages. Stripe, SMTP and shipping = owner connect.",
    mark: "🛒",
    accent: "border-emerald-400/35 bg-emerald-500/[0.08]",
    availability: "available",
    href: "/order/shop",
    agencySection: true,
    fields: [
      ...contactFields,
      {
        id: "store_name",
        label: "Store name",
        required: true,
      },
      {
        id: "goal",
        label: "What will you sell?",
        required: true,
        multiline: true,
        placeholder: "Products, shipping region, payment needs…",
      },
    ] as ServiceField[],
    deliveryNote:
      "After payment you receive a professional online shop in your client cabinet — open it and continue setup.",
    includes: [
      "Modern design for your niche",
      "Catalog, cart, wishlist & search",
      "German legal pages",
      "Client cabinet access",
    ],
    stages: ["Questionnaire", "Register", "Payment", "Shop ready"],
    timeline: "After payment — shop in your cabinet",
    afterPay: ["Online shop in cabinet", "Open Store", "Continue setup"],
    support: "Cabinet + Vector",
  },
  {
    id: "ai_chatbot",
    name: "AI Business Assistant",
    price_label: "from 499 €",
    blurb: "Digital employee for Telegram (more channels coming soon).",
    mark: "🤖",
    accent: "border-sky-400/35 bg-sky-500/[0.08]",
    availability: "available",
    href: "/order/bot",
    agencySection: false,
    fields: [
      ...contactFields,
      {
        id: "website_url",
        label: "Website URL (if any)",
        type: "url",
      },
      {
        id: "goal",
        label: "Where should the bot work?",
        required: true,
        multiline: true,
        placeholder: "Site chat, WhatsApp, Telegram…",
      },
    ],
    deliveryNote: "Bot setup project in cabinet (or full Digital Employee wizard).",
    includes: ["AI employee setup", "Channel plan", "Cabinet workspace"],
    stages: ["Form", "Payment", "Setup", "Connect"],
    timeline: "3–10 days",
    afterPay: ["Project in cabinet", "Optional upgrade to full bot packages"],
    support: "Cabinet + Vector",
  },
  {
    id: "business_automation",
    name: "Business Automation",
    price_label: "from 399 €",
    blurb: "Automate recurring SMB workflows.",
    mark: "⚡",
    accent: "border-violet-400/30 bg-violet-500/[0.06]",
    availability: "available",
    href: "/order/service/business_automation",
    agencySection: true,
    fields: urlGoal(
      "Which process should we automate?",
      "Leads, reminders, invoices, handoffs…",
    ),
    deliveryNote: "Automation plan and build status in cabinet.",
    includes: ["Process map", "Automation build", "Cabinet status"],
    stages: ["Form", "Payment", "Map", "Automate"],
    timeline: "5–14 days",
    afterPay: ["Project in cabinet"],
    support: "Cabinet + Vector",
  },
  {
    id: "ai_social_content",
    name: "AI Social Content",
    price_label: "from 199 €/mo",
    blurb: "Monthly Reels, TikTok, Instagram, Facebook — AI voice & design.",
    mark: "🎬",
    accent: "border-pink-400/30 bg-pink-500/[0.06]",
    availability: "available",
    href: "/order/service/ai_social_content",
    agencySection: true,
    billing: "monthly",
    fields: [
      ...contactFields,
      {
        id: "goal",
        label: "Channels & tone",
        required: true,
        multiline: true,
        placeholder: "Instagram + TikTok, brand voice…",
      },
    ],
    deliveryNote:
      "First month billed now. Recurring Stripe subscription comes next — marked honestly.",
    includes: [
      "Reels",
      "TikTok",
      "Instagram",
      "Facebook",
      "AI voice",
      "AI design",
    ],
    stages: ["Form", "First payment", "Monthly pack"],
    timeline: "ongoing monthly",
    afterPay: ["Project in cabinet", "First content pack"],
    support: "Cabinet + Vector",
  },
  {
    id: "site_maintenance",
    name: "Website Maintenance",
    price_label: "from 49 €/mo",
    blurb: "Updates, backups, monitoring, support — monthly.",
    mark: "🛠",
    accent: "border-zinc-400/30 bg-zinc-500/[0.06]",
    availability: "available",
    href: "/order/service/site_maintenance",
    agencySection: true,
    billing: "monthly",
    fields: urlGoal("Site to maintain", "URL + access notes after pay…"),
    deliveryNote: "First month billed now. Recurring later.",
    includes: ["Updates", "Backups", "Monitoring", "Support"],
    stages: ["Form", "First payment", "Care plan"],
    timeline: "ongoing monthly",
    afterPay: ["Maintenance case in cabinet"],
    support: "Cabinet + Vector",
  },
  {
    id: "ai_seo_monitoring",
    name: "AI SEO Monitoring",
    price_label: "from 29 €/mo",
    blurb: "Ongoing rank control and improvement tips.",
    mark: "📈",
    accent: "border-emerald-400/30 bg-emerald-500/[0.06]",
    availability: "available",
    href: "/order/service/ai_seo_monitoring",
    agencySection: true,
    billing: "monthly",
    fields: urlGoal("Keywords / region", "Local SEO focus…"),
    deliveryNote: "First month billed now. Recurring later.",
    includes: ["Rank snapshot", "AI tips", "Cabinet updates"],
    stages: ["Form", "First payment", "Monitoring"],
    timeline: "ongoing monthly",
    afterPay: ["Monitoring case in cabinet"],
    support: "Cabinet + Vector",
  },
];

export function getServiceSpec(id: string): ServiceSpec | undefined {
  return SERVICE_SPECS.find((s) => s.id === id);
}

export const HUB_PRIMARY_SERVICE_IDS = [
  "landing_website",
  "ecommerce_shop",
  "ai_business_bot",
  "website_check",
] as const;

/** Premium Website Services block on storefront — existing-site add-ons (not primary SKUs). */
export const HUB_AGENCY_SERVICE_IDS = SERVICE_SPECS.filter(
  (s) =>
    s.agencySection &&
    !["ecommerce_shop", "ai_chatbot", "landing_website"].includes(s.id),
).map((s) => s.id);

export const HUB_MORE_SERVICE_IDS = [
  "website_repair",
  "ai_website_analysis",
  "seo_audit",
  "speed_optimization",
  "security_check",
  "google_business_setup",
  "website_migration",
  "reputation_audit",
  "business_automation",
  "ai_social_content",
  "site_maintenance",
  "ai_seo_monitoring",
] as const;
