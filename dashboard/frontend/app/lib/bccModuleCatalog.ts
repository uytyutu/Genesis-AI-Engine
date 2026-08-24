/**
 * BCC 2.0 — Product-first module catalog (SSOT for Meine Produkte / Übersicht).
 *
 * availability:
 *   live        → Nicht aktiviert → Hinzufügen (real purchase/order path)
 *   coming_soon → Coming Soon (no fake Hinzufügen)
 */

import {
  honestStatusDisplay,
  resolveHonestCta,
  resolveOrderHonestStatus,
  type HonestCta,
  type HonestProductStatus,
  type HonestStatusDisplay,
  type OrderStatusInput,
} from "./clientProductStatus";
import type { OwnedSignals } from "./clientServiceMarketplace";

export type BccModuleAvailability = "live" | "coming_soon";

export type BccModuleDetect =
  | "website"
  | "store"
  | "bot"
  | "auditor"
  | "backup"
  | "analytics"
  | "crm"
  | "marketing"
  | "domain"
  | "booking"
  | "automation"
  | "seo";

export type BccModuleDef = {
  id: string;
  icon: string;
  label: string;
  detect: BccModuleDetect;
  availability: BccModuleAvailability;
  ownedHref: string;
  purchaseHref: string | null;
  priceHint?: string;
  /** Shown on Übersicht primary strip */
  primary?: boolean;
};

/** Core + honest add-ons. Only `live` rows may show Hinzufügen. */
export const BCC_MODULE_CATALOG: readonly BccModuleDef[] = [
  {
    id: "website",
    icon: "🌐",
    label: "Website",
    detect: "website",
    availability: "live",
    ownedHref: "/client/site",
    purchaseHref: "/order?form=1",
    priceHint: "Ab 199 €",
    primary: true,
  },
  {
    id: "shop",
    icon: "🛒",
    label: "Online Shop",
    detect: "store",
    availability: "live",
    ownedHref: "/client/products",
    purchaseHref: "/order/shop",
    priceHint: "Ab 799 €",
    primary: true,
  },
  {
    id: "ai",
    icon: "🤖",
    label: "AI Assistant",
    detect: "bot",
    availability: "live",
    ownedHref: "/client/bots",
    purchaseHref: "/order/bot",
    priceHint: "Ab 499 €",
    primary: true,
  },
  {
    id: "auditor",
    icon: "🔍",
    label: "Website Auditor",
    detect: "auditor",
    availability: "live",
    ownedHref: "/client/analyses",
    purchaseHref: "/site?service=analysis",
    priceHint: "Kostenloser Check",
  },
  {
    id: "backup",
    icon: "💾",
    label: "Downloads / ZIP",
    detect: "backup",
    availability: "live",
    ownedHref: "/client/downloads",
    purchaseHref: "/client/downloads",
    priceHint: "Im Workspace",
  },
  {
    id: "analytics",
    icon: "📊",
    label: "Analytics",
    detect: "analytics",
    availability: "live",
    ownedHref: "/client/analytics",
    purchaseHref: "/client/analytics",
    priceHint: "Verbinden",
  },
  {
    id: "crm",
    icon: "👥",
    label: "CRM",
    detect: "crm",
    availability: "coming_soon",
    ownedHref: "/client/crm",
    purchaseHref: null,
  },
  {
    id: "marketing",
    icon: "📣",
    label: "Marketing",
    detect: "marketing",
    availability: "coming_soon",
    ownedHref: "/client/campaigns",
    purchaseHref: null,
  },
  {
    id: "domain",
    icon: "🌍",
    label: "Domain",
    detect: "domain",
    availability: "coming_soon",
    ownedHref: "/client/domain",
    purchaseHref: null,
  },
  {
    id: "booking",
    icon: "📅",
    label: "Booking",
    detect: "booking",
    availability: "coming_soon",
    ownedHref: "/client/booking",
    purchaseHref: null,
  },
  {
    id: "automation",
    icon: "⚡",
    label: "Automation",
    detect: "automation",
    availability: "coming_soon",
    ownedHref: "/client/automations",
    purchaseHref: null,
  },
  {
    id: "seo",
    icon: "📈",
    label: "SEO",
    detect: "seo",
    availability: "coming_soon",
    ownedHref: "/client/shop",
    purchaseHref: null,
  },
] as const;

export type BccModuleCardModel = {
  id: string;
  icon: string;
  title: string;
  packageLine: string | null;
  status: HonestStatusDisplay;
  cta: HonestCta;
  ctaHref: string | null;
  priceHint?: string;
};

function ownedByDetect(detect: BccModuleDetect, signals: OwnedSignals): boolean {
  switch (detect) {
    case "website":
      return Boolean(signals.hasWebsite);
    case "store":
      return Boolean(signals.hasStore);
    case "bot":
      return Boolean(signals.hasBot);
    case "auditor":
      return Boolean(signals.hasAuditor);
    case "backup":
      return Boolean(signals.hasBackup || signals.hasWebsite);
    case "seo":
      return Boolean(signals.hasSeo);
    case "automation":
      return Boolean(signals.hasAutomation);
    case "domain":
      return Boolean(signals.hasDomainPublished);
    case "analytics":
      return Boolean(signals.hasAnalyticsSurface);
    default:
      return false;
  }
}

export type BccModuleResolveInput = {
  signals: OwnedSignals;
  /** Optional order status for primary products (pending vs active). */
  websiteOrder?: OrderStatusInput | null;
  shopOrder?: OrderStatusInput | null;
  botOrder?: OrderStatusInput | null;
  websiteManageHref?: string | null;
  shopManageHref?: string | null;
  packageLine?: Partial<Record<"website" | "shop" | "ai", string | null>>;
};

function statusForModule(
  def: BccModuleDef,
  input: BccModuleResolveInput,
): HonestProductStatus {
  if (def.availability === "coming_soon") {
    return "coming_soon";
  }
  if (def.detect === "analytics") {
    const s = input.signals;
    if (!s.hasWebsite && !s.hasStore && !s.hasBot) return "coming_soon";
    if (s.hasAnalyticsSurface) return "active";
    return "not_activated";
  }
  if (def.detect === "website" && input.websiteOrder) {
    return resolveOrderHonestStatus(input.websiteOrder).key;
  }
  if (def.detect === "store" && input.shopOrder) {
    return resolveOrderHonestStatus(input.shopOrder).key;
  }
  if (def.detect === "bot" && input.botOrder) {
    return resolveOrderHonestStatus(input.botOrder).key;
  }
  if (ownedByDetect(def.detect, input.signals)) return "active";
  return "not_activated";
}

function hrefForModule(
  def: BccModuleDef,
  status: HonestProductStatus,
  input: BccModuleResolveInput,
): string | null {
  if (status === "coming_soon" || status === "unknown") return null;
  if (status === "active" || status === "pending") {
    if (def.detect === "website" && input.websiteManageHref) {
      return input.websiteManageHref;
    }
    if (def.detect === "store" && input.shopManageHref) {
      return input.shopManageHref;
    }
    return def.ownedHref;
  }
  return def.purchaseHref;
}

/** Resolve full catalog cards for Meine Produkte. */
export function resolveBccModuleCards(
  input: BccModuleResolveInput,
): BccModuleCardModel[] {
  return BCC_MODULE_CATALOG.map((def) => {
    const statusKey = statusForModule(def, input);
    let status = honestStatusDisplay(statusKey);
    // Analytics connection language (not product "Nicht aktiviert")
    if (def.id === "analytics" && statusKey === "not_activated") {
      status = {
        ...status,
        label: "Nicht verbunden",
      };
    }
    const cta = resolveHonestCta(statusKey);
    // Analytics connection language (not product "Nicht aktiviert")
    const ctaFixed =
      def.id === "analytics" && statusKey === "not_activated"
        ? {
            kind: "add" as const,
            label: "Analytics hinzufügen →",
            actionable: true,
          }
        : cta;
    const ctaHref = ctaFixed.actionable
      ? hrefForModule(def, statusKey, input)
      : null;
    const packageLine =
      statusKey === "not_activated" || statusKey === "coming_soon"
        ? null
        : def.detect === "website"
          ? input.packageLine?.website ?? null
          : def.detect === "store"
            ? input.packageLine?.shop ?? null
            : def.detect === "bot"
              ? input.packageLine?.ai ?? null
              : null;

    return {
      id: def.id,
      icon: def.icon,
      title: def.label,
      packageLine,
      status,
      cta: ctaHref ? ctaFixed : { ...ctaFixed, actionable: false },
      ctaHref,
      priceHint:
        statusKey === "not_activated" && def.availability === "live"
          ? def.priceHint
          : undefined,
    };
  });
}

/** Overview strip — primary live modules only. */
export function resolveBccPrimaryCards(
  input: BccModuleResolveInput,
): BccModuleCardModel[] {
  return resolveBccModuleCards(input).filter((c) =>
    BCC_MODULE_CATALOG.some((d) => d.id === c.id && d.primary),
  );
}
