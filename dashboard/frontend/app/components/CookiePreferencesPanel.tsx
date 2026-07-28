"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  COOKIE_CONSENT_EVENT,
  acceptAllCookies,
  acceptEssentialOnly,
  cookieConsentPolicyLabel,
  defaultConsentDraft,
  readCookieConsent,
  writeCookieConsent,
  type CookieConsentState,
} from "../lib/cookieConsent";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * Inline Privacy & Cookies controls for /client/privacy (and reusable panels).
 */
export function CookiePreferencesPanel({
  compact = false,
}: {
  compact?: boolean;
}) {
  const [state, setState] = useState<CookieConsentState | null>(null);
  const [draft, setDraft] = useState<CookieConsentState>(defaultConsentDraft);
  const [saved, setSaved] = useState(false);

  const refresh = useCallback(() => {
    const current = readCookieConsent();
    setState(current);
    setDraft(
      current
        ? { ...current }
        : { ...defaultConsentDraft(), analytics: false, marketing: false },
    );
  }, []);

  useEffect(() => {
    refresh();
    const onChange = () => refresh();
    window.addEventListener(COOKIE_CONSENT_EVENT, onChange);
    return () => window.removeEventListener(COOKIE_CONSENT_EVENT, onChange);
  }, [refresh]);

  function applySaved(written: CookieConsentState) {
    setState(written);
    setDraft({ ...written });
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  }

  function persistCustom() {
    applySaved(
      writeCookieConsent({
        analytics: draft.analytics,
        marketing: draft.marketing,
        source: "custom",
      }),
    );
  }

  return (
    <div
      className={
        compact
          ? "space-y-3"
          : "space-y-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5"
      }
    >
      <div>
        <h2 className="text-base font-semibold text-white">Privacy & Cookies</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Essential cookies always on for {BRAND_NAME}. Analytics and Marketing
          only with your consent. Policy version:{" "}
          <span className="text-zinc-300">{cookieConsentPolicyLabel()}</span>
          . After a material policy update the version increases and the banner
          asks again.
        </p>
        <p className="mt-2 text-xs text-zinc-500">
          Legal:{" "}
          <Link href="/cookies" className="text-sky-300 underline">
            Cookie-Richtlinie
          </Link>
          {" · "}
          <Link href="/datenschutz" className="text-sky-300 underline">
            Datenschutz
          </Link>
        </p>
      </div>

      {!state ? (
        <p className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
          Выбор ещё не сохранён для этой версии политики — укажите предпочтения
          ниже.
        </p>
      ) : (
        <p className="text-xs text-zinc-500">
          Последний выбор: {state.source.replace("_", " ")} ·{" "}
          {state.decidedAt
            ? new Date(state.decidedAt).toLocaleString()
            : "—"}
        </p>
      )}

      <div className="space-y-3 text-sm">
        <label className="flex items-start gap-3 text-zinc-200">
          <input type="checkbox" checked disabled className="mt-1" />
          <span>
            <span className="font-medium text-white">Essential</span>
            <span className="mt-0.5 block text-xs text-zinc-500">
              Всегда включены — сессия, безопасность, личный кабинет.
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
            <span className="font-medium text-white">Analytics</span>
            <span className="mt-0.5 block text-xs text-zinc-500">
              По согласию — понимание использования сервиса.
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
            <span className="font-medium text-white">Marketing</span>
            <span className="mt-0.5 block text-xs text-zinc-500">
              По согласию — реклама и ретаргетинг.
            </span>
          </span>
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => persistCustom()}
          className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
        >
          Сохранить выбор
        </button>
        <button
          type="button"
          onClick={() => applySaved(acceptAllCookies())}
          className="rounded-xl border border-white/20 px-4 py-2 text-sm text-white hover:bg-white/5"
        >
          Принять все
        </button>
        <button
          type="button"
          onClick={() => applySaved(acceptEssentialOnly())}
          className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
        >
          Только необходимые
        </button>
      </div>
      {saved ? (
        <p className="text-xs text-emerald-300">Сохранено.</p>
      ) : null}
    </div>
  );
}
