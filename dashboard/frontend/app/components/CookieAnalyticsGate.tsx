"use client";

import { useEffect } from "react";
import {
  COOKIE_CONSENT_EVENT,
  isCookieCategoryAllowed,
  runWhenCookieAllowed,
} from "../lib/cookieConsent";

/**
 * Mount once in the app tree. Today: no third-party scripts.
 * When adding GA / Meta Pixel / Clarity — register loaders here behind consent.
 */
export function CookieAnalyticsGate() {
  useEffect(() => {
    const run = () => {
      runWhenCookieAllowed("analytics", () => {
        // Placeholder: load GA / Clarity only after analytics consent.
        // Example: injectScript("https://www.googletagmanager.com/gtag/js?id=G-…")
      });
      runWhenCookieAllowed("marketing", () => {
        // Placeholder: load Meta Pixel / ads pixels only after marketing consent.
      });
    };
    run();
    window.addEventListener(COOKIE_CONSENT_EVENT, run);
    return () => window.removeEventListener(COOKIE_CONSENT_EVENT, run);
  }, []);

  // Expose for debugging / future tags (no secrets)
  useEffect(() => {
    if (typeof window === "undefined") return;
    (window as unknown as { __virtusCookieAllowed?: (c: string) => boolean }).__virtusCookieAllowed =
      (c: string) =>
        c === "essential" ||
        c === "analytics" ||
        c === "marketing"
          ? isCookieCategoryAllowed(c as "essential" | "analytics" | "marketing")
          : false;
  }, []);

  return null;
}
