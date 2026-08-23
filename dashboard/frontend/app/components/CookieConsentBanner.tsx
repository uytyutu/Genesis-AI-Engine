"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  acceptAllCookies,
  acceptEssentialOnly,
  cookieConsentPolicyLabel,
  hasCookieDecision,
  readCookieConsent,
  writeCookieConsent,
  type CookieConsentState,
  defaultConsentDraft,
} from "../lib/cookieConsent";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * EU-ready cookie banner — Essential always on; Analytics / Marketing opt-in.
 * Copy follows UI language (Language Constitution) — never hardcode one locale.
 */
export function CookieConsentBanner() {
  const { t } = useTranslation("site");
  const [visible, setVisible] = useState(false);
  const [customize, setCustomize] = useState(false);
  const [draft, setDraft] = useState<CookieConsentState>(defaultConsentDraft);

  const openPanel = useCallback((forceCustomize = false) => {
    const existing = readCookieConsent();
    setDraft(
      existing
        ? { ...existing }
        : { ...defaultConsentDraft(), analytics: false, marketing: false },
    );
    setCustomize(forceCustomize || false);
    setVisible(true);
  }, []);

  useEffect(() => {
    if (!hasCookieDecision()) {
      setVisible(true);
    }
    const onOpen = () => openPanel(true);
    window.addEventListener("virtus:cookie-preferences-open", onOpen);
    return () =>
      window.removeEventListener("virtus:cookie-preferences-open", onOpen);
  }, [openPanel]);

  function closeAfter(save: () => void) {
    save();
    setVisible(false);
    setCustomize(false);
  }

  if (!visible) return null;

  return (
    <div
      data-cookie-consent="1"
      className="fixed inset-x-0 bottom-0 z-[80] p-3 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-consent-title"
      aria-describedby="cookie-consent-desc"
    >
      <div className="mx-auto max-w-2xl rounded-2xl border border-white/15 bg-[#0c1220]/95 p-4 shadow-2xl backdrop-blur-md sm:p-5">
        <p
          id="cookie-consent-title"
          className="text-base font-semibold text-white"
        >
          {t("cookies.title")}
        </p>
        <p
          id="cookie-consent-desc"
          className="mt-2 text-sm leading-relaxed text-zinc-300"
        >
          {t("cookies.body", { brand: BRAND_NAME })}
        </p>
        <p className="mt-2 text-xs text-zinc-500">
          {t("cookies.more")}{" "}
          <Link href="/cookies" className="text-sky-300 underline hover:text-sky-200">
            {t("cookies.policy")}
          </Link>
          {" · "}
          <Link
            href="/datenschutz"
            className="text-sky-300 underline hover:text-sky-200"
          >
            {t("cookies.privacy")}
          </Link>
          {" · "}
          <Link
            href="/client/privacy"
            className="text-sky-300 underline hover:text-sky-200"
          >
            {t("cookies.cabinetPrivacy")}
          </Link>
          {" · "}
          {cookieConsentPolicyLabel()}
        </p>

        {customize ? (
          <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-black/30 p-3 text-sm">
            <label className="flex items-start gap-3 text-zinc-200">
              <input type="checkbox" checked disabled className="mt-1" />
              <span>
                <span className="font-medium text-white">{t("cookies.essential")}</span>
                <span className="mt-0.5 block text-xs text-zinc-500">
                  {t("cookies.essentialHint")}
                </span>
              </span>
            </label>
            <label className="flex items-start gap-3 text-zinc-200">
              <input
                type="checkbox"
                className="mt-1"
                checked={draft.analytics}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, analytics: e.target.checked }))
                }
              />
              <span>
                <span className="font-medium text-white">{t("cookies.analytics")}</span>
                <span className="mt-0.5 block text-xs text-zinc-500">
                  {t("cookies.analyticsHint")}
                </span>
              </span>
            </label>
            <label className="flex items-start gap-3 text-zinc-200">
              <input
                type="checkbox"
                className="mt-1"
                checked={draft.marketing}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, marketing: e.target.checked }))
                }
              />
              <span>
                <span className="font-medium text-white">{t("cookies.marketing")}</span>
                <span className="mt-0.5 block text-xs text-zinc-500">
                  {t("cookies.marketingHint")}
                </span>
              </span>
            </label>
          </div>
        ) : null}

        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <button
            type="button"
            onClick={() => closeAfter(() => acceptAllCookies())}
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
          >
            {t("cookies.acceptAll")}
          </button>
          <button
            type="button"
            onClick={() => closeAfter(() => acceptEssentialOnly())}
            className="rounded-xl border border-white/20 bg-white/5 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10"
          >
            {t("cookies.essentialOnly")}
          </button>
          {customize ? (
            <button
              type="button"
              onClick={() =>
                closeAfter(() =>
                  writeCookieConsent({
                    analytics: draft.analytics,
                    marketing: draft.marketing,
                    source: "custom",
                  }),
                )
              }
              className="rounded-xl border border-sky-400/40 bg-sky-500/15 px-4 py-2.5 text-sm font-medium text-sky-100 hover:bg-sky-500/25"
            >
              {t("cookies.save")}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setCustomize(true)}
              className="rounded-xl border border-white/15 px-4 py-2.5 text-sm text-zinc-300 hover:bg-white/5"
            >
              {t("cookies.customize")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
