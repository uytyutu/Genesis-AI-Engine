/**
 * B4.0 — Vector Business Companion contracts (scope lock, FE mirror).
 *
 * No turn pipeline / research / actions here — types + constants only.
 * SSOT for runtime remains backend companion_contracts.py + GET /api/client/context.
 */

export const B4_ENGINE = "b4_vector_companion_v1" as const;
export const CONTEXT_ENGINE_REQUIRED = "b3_client_context_v1" as const;
export const CONTEXT_PATH = "/api/client/context" as const;
/** B4.1 — tenant-safe companion context (auth → Context SSOT). */
export const COMPANION_CONTEXT_PATH =
  "/api/client/vector/companion-context" as const;
/** B4.2 — READ conversation turn (Context-grounded). */
export const COMPANION_TURN_PATH = "/api/client/vector/companion-turn" as const;

export const B4_SLICE_ORDER = [
  "B4.0",
  "B4.1",
  "B4.2",
  "B4.3",
  "B4.4",
  "B4.5",
  "B4.6",
  "B4.7",
] as const;

export type CompanionIntent = "read" | "clarify" | "research" | "action";

export type CompanionLocation =
  | "dashboard"
  | "products"
  | "website"
  | "shop"
  | "analytics"
  | "settings"
  | "support"
  | "billing"
  | "other";

/** Primary BCC entry — persistent dock, not a separate Vector page. */
export const ENTRY_SURFACE = "VectorDialogDock" as const;
export const ASSISTANT_NAME = "Vector" as const;
export const DEFAULT_GREETING_DE =
  "Guten Tag! Ich bin Vector, dein Business Assistant." as const;

export const CONFIRM_CTA_LABEL = "Übernehmen" as const;
export const CONFIRM_CANCEL_LABEL = "Abbrechen" as const;

export const FIRST_ACTION_KINDS = [
  "navigate",
  "live_website_capability",
  "live_store_capability",
] as const;

export type FirstActionKind = (typeof FIRST_ACTION_KINDS)[number];

export const RESEARCH_SOURCE_KIND = "external" as const;
export const RESEARCH_DISCLAIMER_DE =
  "Externe Information (Web Research) — nicht aus Ihren Virtus-Core-Daten." as const;

export type ResearchSource = {
  title: string;
  url: string;
  retrieved_at: string;
  kind: typeof RESEARCH_SOURCE_KIND;
  disclaimer?: string;
};

export type ActionProposal = {
  proposal_id: string;
  kind: FirstActionKind | string;
  capability_id?: string | null;
  label: string;
  summary: string;
  href?: string | null;
  section?: string | null;
  irreversible?: boolean;
  confirm_label?: string;
  cancel_label?: string;
};

export type CompanionTurnResponse = {
  ok: boolean;
  engine: typeof B4_ENGINE | string;
  intent: CompanionIntent;
  assistant: string;
  message: string;
  clarify_question?: string | null;
  context_ref?: { path: string; engine: string; period?: string };
  cited_read_scopes?: string[];
  research_sources?: ResearchSource[];
  research_disclaimer?: string | null;
  action_proposal?: ActionProposal | null;
  location?: CompanionLocation;
  honesty?: string;
  entry_surface?: typeof ENTRY_SURFACE | string;
};

export function locationFromPath(path: string | null | undefined): CompanionLocation {
  const p = (path || "").replace(/\/$/, "") || "/client";
  const rules: [string, CompanionLocation][] = [
    ["/client/analytics", "analytics"],
    ["/client/stats", "analytics"],
    ["/client/site", "website"],
    ["/client/website", "website"],
    ["/client/shop", "shop"],
    ["/client/products", "products"],
    ["/client/settings", "settings"],
    ["/client/support", "support"],
    ["/client/billing", "billing"],
  ];
  for (const [prefix, loc] of rules) {
    if (p === prefix || p.startsWith(`${prefix}/`)) return loc;
  }
  if (p === "/client" || p.startsWith("/client")) return "dashboard";
  return "other";
}
