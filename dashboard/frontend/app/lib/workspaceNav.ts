/**
 * Workspace nav SSOT — Standalone vs Connected (one panel).
 * Mirrors backend commerce_gates.workspace_nav_spec.
 */

export type CommerceMode = "standalone" | "connected";

export type WorkspaceNavItem = {
  id: string;
  href: string;
  label: string;
  match: (p: string) => boolean;
  /** Connected-only — show locked CTA when not ecosystem */
  connectedOnly?: boolean;
  /** Requires store ownership */
  storeOnly?: boolean;
  comingSoon?: boolean;
  group: "core" | "store" | "ecosystem" | "account";
};

export const WORKSPACE_NAV: WorkspaceNavItem[] = [
  {
    id: "dashboard",
    href: "/client",
    label: "Dashboard",
    match: (p) => p === "/client",
    group: "core",
  },
  {
    id: "site",
    href: "/client/site",
    label: "Мой сайт",
    match: (p) => p.startsWith("/client/site") || p.startsWith("/client/websites"),
    group: "core",
  },
  {
    id: "pages",
    href: "/client/pages",
    label: "Страницы",
    match: (p) => p.startsWith("/client/pages"),
    group: "core",
  },
  {
    id: "media",
    href: "/client/media",
    label: "Медиа",
    match: (p) => p.startsWith("/client/media"),
    group: "core",
  },
  {
    id: "texts",
    href: "/client/texts",
    label: "Тексты",
    match: (p) => p.startsWith("/client/texts"),
    group: "core",
  },
  {
    id: "contacts",
    href: "/client/contacts",
    label: "Контакты",
    match: (p) => p.startsWith("/client/contacts"),
    group: "core",
  },
  {
    id: "products",
    href: "/client/products",
    label: "Товары",
    match: (p) => p.startsWith("/client/products") || p.startsWith("/client/stores"),
    storeOnly: true,
    group: "store",
  },
  {
    id: "orders",
    href: "/client/orders",
    label: "Заказы",
    match: (p) => p.startsWith("/client/orders"),
    storeOnly: true,
    group: "store",
  },
  {
    id: "settings",
    href: "/client/settings",
    label: "Настройки",
    match: (p) => p.startsWith("/client/settings"),
    group: "core",
  },
  {
    id: "backup",
    href: "/client/downloads",
    label: "Резервная копия",
    match: (p) => p.startsWith("/client/downloads"),
    group: "core",
  },
  {
    id: "domain",
    href: "/client/domain",
    label: "Домен",
    match: (p) => p.startsWith("/client/domain"),
    group: "core",
  },
  {
    id: "stats_basic",
    href: "/client/stats",
    label: "Статистика",
    match: (p) => p.startsWith("/client/stats") && !p.startsWith("/client/analytics"),
    group: "core",
  },
  {
    id: "marketplace",
    href: "/client/shop",
    label: "Расширьте бизнес",
    match: (p) => p.startsWith("/client/shop"),
    group: "account",
  },
  // Connected extras
  {
    id: "ai_assistant",
    href: "/client/ai",
    label: "Virtus AI",
    match: (p) => p.startsWith("/client/ai"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "crm",
    href: "/client/crm",
    label: "CRM",
    match: (p) => p.startsWith("/client/crm"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "analytics",
    href: "/client/analytics",
    label: "Аналитика",
    match: (p) => p.startsWith("/client/analytics"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "chatbots",
    href: "/client/bots",
    label: "Чат-боты",
    match: (p) => p.startsWith("/client/bots"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "automations",
    href: "/client/automations",
    label: "Автоматизации",
    match: (p) => p.startsWith("/client/automations"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "email_marketing",
    href: "/client/email",
    label: "Email-маркетинг",
    match: (p) => p.startsWith("/client/email"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "whatsapp",
    href: "/client/whatsapp",
    label: "WhatsApp",
    match: (p) => p.startsWith("/client/whatsapp"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "booking",
    href: "/client/booking",
    label: "Бронирование",
    match: (p) => p.startsWith("/client/booking"),
    connectedOnly: true,
    group: "ecosystem",
  },
  {
    id: "notifications",
    href: "/client/notifications",
    label: "Уведомления",
    match: (p) => p.startsWith("/client/notifications"),
    connectedOnly: true,
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
  {
    id: "billing",
    href: "/client/billing",
    label: "Биллинг",
    match: (p) => p.startsWith("/client/billing"),
    group: "account",
  },
  {
    id: "support",
    href: "/client/support",
    label: "Поддержка",
    match: (p) => p.startsWith("/client/support"),
    group: "account",
  },
];

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
