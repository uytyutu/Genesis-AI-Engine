/**
 * Cookie consent (EU-ready) — Essential always on; Analytics / Marketing opt-in.
 *
 * Versioning (CEO):
 *   COOKIE_CONSENT_POLICY_VERSION = 1  → storage key virtus_cookie_consent_v1
 *   After a material Cookie-Richtlinie / category change, set it to 2:
 *     export const COOKIE_CONSENT_POLICY_VERSION = 2 as const;
 *   Then users without virtus_cookie_consent_v2 see the banner again.
 *   Old v1 keys are left in place but ignored (no migration of opt-in).
 */

export type CookieCategory = "essential" | "analytics" | "marketing";

/** Bump after material policy / category changes (1 → 2 → …). */
export const COOKIE_CONSENT_POLICY_VERSION = 1 as const;

export type CookieConsentState = {
  version: number;
  essential: true;
  analytics: boolean;
  marketing: boolean;
  decidedAt: string;
  /** how the choice was made */
  source: "accept_all" | "essential_only" | "custom";
};

export const COOKIE_CONSENT_EVENT = "virtus:cookie-consent";

export function cookieConsentStorageKey(
  version: number = COOKIE_CONSENT_POLICY_VERSION,
): string {
  return `virtus_cookie_consent_v${version}`;
}

/** Canonical key for the active policy version (e.g. virtus_cookie_consent_v1). */
export const COOKIE_CONSENT_KEY = cookieConsentStorageKey(
  COOKIE_CONSENT_POLICY_VERSION,
);

const EMPTY: CookieConsentState = {
  version: COOKIE_CONSENT_POLICY_VERSION,
  essential: true,
  analytics: false,
  marketing: false,
  decidedAt: "",
  source: "essential_only",
};

function isConsentSource(
  value: unknown,
): value is CookieConsentState["source"] {
  return (
    value === "accept_all" ||
    value === "essential_only" ||
    value === "custom"
  );
}

/**
 * Read consent for the *current* policy version only.
 * Older versions (v1 when current is v2, etc.) return null → banner again.
 */
export function readCookieConsent(): CookieConsentState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as Partial<CookieConsentState>;
    if (!data || typeof data.version !== "number") return null;
    if (data.version !== COOKIE_CONSENT_POLICY_VERSION) return null;
    return {
      version: COOKIE_CONSENT_POLICY_VERSION,
      essential: true,
      analytics: Boolean(data.analytics),
      marketing: Boolean(data.marketing),
      decidedAt: String(data.decidedAt || ""),
      source: isConsentSource(data.source) ? data.source : "custom",
    };
  } catch {
    return null;
  }
}

export function hasCookieDecision(): boolean {
  return readCookieConsent() !== null;
}

/** True when user must see the banner again (no decision for current policy version). */
export function cookieConsentNeedsReconsent(): boolean {
  return !hasCookieDecision();
}

export function isCookieCategoryAllowed(category: CookieCategory): boolean {
  if (category === "essential") return true;
  const state = readCookieConsent();
  if (!state) return false;
  return category === "analytics" ? state.analytics : state.marketing;
}

export function writeCookieConsent(
  patch: Pick<CookieConsentState, "analytics" | "marketing" | "source">,
): CookieConsentState {
  const state: CookieConsentState = {
    version: COOKIE_CONSENT_POLICY_VERSION,
    essential: true,
    analytics: Boolean(patch.analytics),
    marketing: Boolean(patch.marketing),
    decidedAt: new Date().toISOString(),
    source: patch.source,
  };
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(state));
      window.dispatchEvent(
        new CustomEvent(COOKIE_CONSENT_EVENT, { detail: state }),
      );
    } catch {
      /* ignore quota / private mode */
    }
  }
  return state;
}

export function acceptAllCookies(): CookieConsentState {
  return writeCookieConsent({
    analytics: true,
    marketing: true,
    source: "accept_all",
  });
}

export function acceptEssentialOnly(): CookieConsentState {
  return writeCookieConsent({
    analytics: false,
    marketing: false,
    source: "essential_only",
  });
}

/** Call when wiring GA / Meta Pixel / Clarity — no-op until user opts in. */
export function runWhenCookieAllowed(
  category: Exclude<CookieCategory, "essential">,
  fn: () => void,
): boolean {
  if (!isCookieCategoryAllowed(category)) return false;
  try {
    fn();
    return true;
  } catch {
    return false;
  }
}

export function openCookiePreferences(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("virtus:cookie-preferences-open"));
}

export function defaultConsentDraft(): CookieConsentState {
  return { ...EMPTY, decidedAt: "" };
}

/** Human-readable active policy label for Privacy settings UI. */
export function cookieConsentPolicyLabel(): string {
  return `v${COOKIE_CONSENT_POLICY_VERSION}`;
}
