/**
 * Workspace nav SSOT — Business Control Center IA (B3).
 * Labels default DE; ClientWorkspaceShell overrides via workspaceCopy.
 */

export type CommerceMode = "standalone" | "connected";

export type WorkspaceNavGroup =
  | "overview"
  | "products"
  | "website"
  | "shop"
  | "ai"
  | "business"
  | "finance"
  | "support"
  | "ecosystem";

export type WorkspaceNavItem = {
  id: string;
  href: string;
  label: string;
  match: (p: string) => boolean;
  /** Connected-only — show locked CTA when not ecosystem */
  connectedOnly?: boolean;
  /** Requires store ownership (legacy; prefer always-visible products) */
  storeOnly?: boolean;
  comingSoon?: boolean;
  /** Primary BCC sidebar / mobile tabs */
  primary?: boolean;
  group: WorkspaceNavGroup;
};

/**
 * BCC primary order + secondary chips.
 * Honesty: comingSoon items stay reachable but badge Coming Soon.
 */
export const WORKSPACE_NAV: WorkspaceNavItem[] = [
  {
    id: "dashboard",
    href: "/client",
    label: "Übersicht",
    match: (p) => p === "/client",
    primary: true,
    group: "overview",
  },
  {
    id: "products",
    href: "/client/products",
    label: "Meine Produkte",
    match: (p) =>
      p.startsWith("/client/products") || p.startsWith("/client/licenses"),
    primary: true,
    group: "products",
  },
  {
    id: "site",
    href: "/client/site",
    label: "Website",
    match: (p) => p.startsWith("/client/site") || p.startsWith("/client/websites"),
    primary: true,
    group: "website",
  },
  {
    id: "pages",
    href: "/client/pages",
    label: "Seiten",
    match: (p) => p.startsWith("/client/pages"),
    comingSoon: true,
    group: "website",
  },
  {
    id: "media",
    href: "/client/media",
    label: "Medien",
    match: (p) => p.startsWith("/client/media"),
    comingSoon: true,
    group: "website",
  },
  {
    id: "texts",
    href: "/client/texts",
    label: "Texte",
    match: (p) => p.startsWith("/client/texts"),
    comingSoon: true,
    group: "website",
  },
  {
    id: "marketplace",
    href: "/client/shop",
    label: "Shop",
    match: (p) => p.startsWith("/client/shop") || p.startsWith("/client/stores"),
    primary: true,
    group: "shop",
  },
  {
    id: "chatbots",
    href: "/client/bots",
    label: "AI",
    match: (p) => p.startsWith("/client/bots") || p.startsWith("/client/ai"),
    primary: true,
    group: "ai",
  },
  {
    id: "inbox",
    href: "/client/inbox",
    label: "Posteingang",
    match: (p) => p.startsWith("/client/inbox"),
    group: "ai",
  },
  {
    id: "ai_assistant",
    href: "/client/ai",
    label: "Virtus AI",
    match: (p) => p === "/client/ai" || p.startsWith("/client/ai/"),
    comingSoon: true,
    group: "ai",
  },
  {
    id: "settings",
    href: "/client/settings",
    label: "Business",
    match: (p) => p.startsWith("/client/settings"),
    primary: true,
    group: "business",
  },
  {
    id: "contacts",
    href: "/client/contacts",
    label: "Kontakte",
    match: (p) => p.startsWith("/client/contacts"),
    comingSoon: true,
    group: "business",
  },
  {
    id: "domain",
    href: "/client/domain",
    label: "Domain",
    match: (p) => p.startsWith("/client/domain"),
    comingSoon: true,
    group: "business",
  },
  {
    id: "orders",
    href: "/client/orders",
    label: "Bestellungen",
    match: (p) => p.startsWith("/client/orders"),
    group: "finance",
  },
  {
    id: "billing",
    href: "/client/billing",
    label: "Abrechnung",
    match: (p) => p.startsWith("/client/billing"),
    primary: true,
    group: "finance",
  },
  {
    id: "backup",
    href: "/client/downloads",
    label: "Downloads",
    match: (p) => p.startsWith("/client/downloads"),
    group: "finance",
  },
  {
    id: "support",
    href: "/client/support",
    label: "Support",
    match: (p) => p.startsWith("/client/support"),
    primary: true,
    group: "support",
  },
  {
    id: "stats_basic",
    href: "/client/stats",
    label: "Statistik",
    match: (p) => p.startsWith("/client/stats") && !p.startsWith("/client/analytics"),
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "crm",
    href: "/client/crm",
    label: "CRM",
    match: (p) => p.startsWith("/client/crm"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "analytics",
    href: "/client/analytics",
    label: "Analytics",
    match: (p) => p.startsWith("/client/analytics"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "automations",
    href: "/client/automations",
    label: "Automation",
    match: (p) => p.startsWith("/client/automations"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "email_marketing",
    href: "/client/email",
    label: "E-Mail-Marketing",
    match: (p) => p.startsWith("/client/email"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "whatsapp",
    href: "/client/whatsapp",
    label: "WhatsApp",
    match: (p) => p.startsWith("/client/whatsapp"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "booking",
    href: "/client/booking",
    label: "Buchung",
    match: (p) => p.startsWith("/client/booking"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "notifications",
    href: "/client/notifications",
    label: "Benachrichtigungen",
    match: (p) => p.startsWith("/client/notifications"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
  {
    id: "campaign_studio",
    href: "/client/campaigns",
    label: "AI Campaign Studio",
    match: (p) => p.startsWith("/client/campaigns"),
    connectedOnly: true,
    comingSoon: true,
    group: "ecosystem",
  },
];

export type BccLocationCrumb = { label: string; href?: string };

/**
 * Resolve “where am I” trail for Client Workspace hubs + admin deep-links.
 * Keeps IA readable: Übersicht → section → action.
 */
export function resolveBccLocationTrail(pathname: string): BccLocationCrumb[] {
  const p = (pathname || "").split("?")[0] || "/client";

  if (p === "/client") return [{ label: "Übersicht" }];

  const websiteAdmin = p.match(/^\/client\/websites\/[^/]+\/admin/);
  if (websiteAdmin) {
    return [
      { label: "Meine Produkte", href: "/client/products" },
      { label: "Website", href: "/client/site" },
      { label: "Verwalten" },
    ];
  }

  const storeAdmin = p.match(/^\/client\/stores\/[^/]+\/admin/);
  if (storeAdmin) {
    return [
      { label: "Meine Produkte", href: "/client/products" },
      { label: "Shop", href: "/client/shop" },
      { label: "Verwalten" },
    ];
  }

  if (p.startsWith("/client/stores/")) {
    return [
      { label: "Meine Produkte", href: "/client/products" },
      { label: "Shop", href: "/client/shop" },
      { label: "Vorschau" },
    ];
  }

  if (p.startsWith("/client/products")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Meine Produkte" },
    ];
  }
  if (p.startsWith("/client/site")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Website" },
    ];
  }
  if (p.startsWith("/client/shop")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Shop" },
    ];
  }
  if (p.startsWith("/client/bots")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "AI", href: "/client/bots" },
      { label: p.includes("/setup") ? "Setup" : "KI-Mitarbeiter" },
    ];
  }
  if (p.startsWith("/client/inbox")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "AI", href: "/client/bots" },
      { label: "Posteingang" },
    ];
  }
  if (p.startsWith("/client/settings")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Business", href: "/client/settings" },
      { label: "Einstellungen" },
    ];
  }
  if (p.startsWith("/client/billing")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Finance", href: "/client/billing" },
      { label: "Abrechnung" },
    ];
  }
  if (p.startsWith("/client/orders")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Finance", href: "/client/billing" },
      { label: "Bestellungen" },
    ];
  }
  if (p.startsWith("/client/downloads")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Finance", href: "/client/billing" },
      { label: "Downloads" },
    ];
  }
  if (p.startsWith("/client/support")) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: "Support" },
    ];
  }

  const hit = WORKSPACE_NAV.find((i) => i.match(p));
  if (hit) {
    return [
      { label: "Übersicht", href: "/client" },
      { label: hit.label, href: hit.comingSoon ? undefined : hit.href },
      ...(hit.comingSoon ? [{ label: "Coming Soon" }] : []),
    ];
  }

  return [
    { label: "Übersicht", href: "/client" },
    { label: "Workspace" },
  ];
}

/** Sidebar + AppShell SSOT — primary BCC links only. */
export function bccPrimaryNav(): WorkspaceNavItem[] {
  return WORKSPACE_NAV.filter((i) => i.primary);
}

/** Mobile bottom tabs — five essentials (Support restored after chip-nav removal). */
export function bccMobileNav(): WorkspaceNavItem[] {
  const ids = ["dashboard", "products", "site", "support", "billing"] as const;
  return ids
    .map((id) => WORKSPACE_NAV.find((i) => i.id === id))
    .filter((i): i is WorkspaceNavItem => Boolean(i));
}

export function filterWorkspaceNav(opts: {
  commerceMode?: CommerceMode | string | null;
  hasStore?: boolean;
  /** When true, show Connected extras unlocked */
  ecosystem?: boolean;
}): WorkspaceNavItem[] {
  const mode = (opts.commerceMode || "standalone").toLowerCase();
  const ecosystem = Boolean(opts.ecosystem) || mode === "connected";
  const hasStore = Boolean(opts.hasStore);

  return WORKSPACE_NAV.filter((item) => {
    if (item.storeOnly && !hasStore) return false;
    if (item.connectedOnly && !ecosystem) return false;
    return true;
  });
}

/** Locked Connected teasers for Standalone (upsell in nav footer). */
export function lockedConnectedTeasers(): WorkspaceNavItem[] {
  return WORKSPACE_NAV.filter((i) => i.connectedOnly && !i.comingSoon).slice(0, 5);
}
