import { resetProjectClaim } from "./projectIdentity";
import { resetGuidedCommerce } from "./guidedCommerce";

const VISITOR_KEY = "genesis_visitor_id";
const OWNER_VISITOR_KEY = "genesis_owner_visitor_id";
const SITE_SESSION_KEY = "vc_public_site_initialized";

export function getVisitorId(scope: "public" | "owner" = "public"): string {
  if (typeof window === "undefined") return "anonymous";
  const key = scope === "owner" ? OWNER_VISITOR_KEY : VISITOR_KEY;
  try {
    let id = localStorage.getItem(key);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(key, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

/** Blind customer test — new visitor + clean project panel state. */
export function beginFreshVisitorSession(scope: "public" | "owner" = "public"): string {
  if (typeof window === "undefined") return "anonymous";
  const key = scope === "owner" ? OWNER_VISITOR_KEY : VISITOR_KEY;
  try {
    const id = crypto.randomUUID();
    localStorage.setItem(key, id);
    for (const storageKey of Object.keys(localStorage)) {
      if (storageKey.startsWith("vc_live_project_")) {
        localStorage.removeItem(storageKey);
      }
    }
    if (scope === "public") {
      resetProjectClaim();
      resetGuidedCommerce();
    }
    window.dispatchEvent(new CustomEvent("genesis:project-state", { detail: null }));
    return id;
  } catch {
    return getVisitorId(scope);
  }
}

/** New tab on /site — fresh cabinet, no foreign project on screen. */
export function initPublicSiteSession(): string {
  if (typeof window === "undefined") return "anonymous";
  try {
    if (!sessionStorage.getItem(SITE_SESSION_KEY)) {
      sessionStorage.setItem(SITE_SESSION_KEY, "1");
      return beginFreshVisitorSession("public");
    }
    return getVisitorId("public");
  } catch {
    return getVisitorId("public");
  }
}
