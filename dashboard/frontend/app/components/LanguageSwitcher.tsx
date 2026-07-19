"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useLocale } from "../context/LocaleContext";
import {
  LOCALE_REGISTRY,
  getLocaleDefinition,
  localeMatchesQuery,
  type AssistantLocale,
  type UiLocale,
} from "../lib/locale/types";

/** Full UI packs — always first on public Path A. */
const PUBLIC_QUICK: readonly UiLocale[] = ["de", "uk", "ru", "en"];

function LocaleSearchList({
  label,
  value,
  onPick,
  translatedOnly = false,
}: {
  label: string;
  value: UiLocale;
  onPick: (code: UiLocale) => void;
  /** Public site: only languages with a real pack (no silent EN fallback). */
  translatedOnly?: boolean;
}) {
  const { t } = useTranslation("common");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const base = translatedOnly
      ? LOCALE_REGISTRY.filter((def) => def.translated)
      : [...LOCALE_REGISTRY].sort((a, b) => Number(b.translated) - Number(a.translated));
    return base.filter((def) => localeMatchesQuery(def, query));
  }, [query, translatedOnly]);

  return (
    <div className="mb-4 last:mb-0">
      <label className="mb-2 block text-xs text-genesis-muted">{label}</label>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={t("language.search")}
        className="mb-2 w-full rounded-lg border border-genesis-border-subtle bg-genesis-bg px-3 py-2 text-sm text-white placeholder:text-genesis-muted/60"
        dir="auto"
        autoComplete="off"
        spellCheck={false}
      />
      <ul
        className="max-h-44 overflow-y-auto rounded-lg border border-genesis-border-subtle bg-genesis-bg/80"
        role="listbox"
        aria-label={label}
      >
        {filtered.length === 0 ? (
          <li className="px-3 py-2 text-xs text-genesis-muted">{t("language.noResults")}</li>
        ) : (
          filtered.map((def) => {
            const active = def.code === value;
            return (
              <li key={def.code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => onPick(def.code)}
                  className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition hover:bg-white/5 ${
                    active ? "bg-genesis-accent/15 text-white" : "text-genesis-text"
                  }`}
                  dir={def.rtl ? "rtl" : "ltr"}
                >
                  <span className="font-medium">{def.nativeName}</span>
                  <span className="shrink-0 text-[10px] uppercase tracking-wide text-genesis-muted">
                    {def.translated ? def.code : `${def.code} · EN`}
                  </span>
                </button>
              </li>
            );
          })
        )}
      </ul>
    </div>
  );
}

export function LanguageSwitcher({
  compact = false,
}: {
  /** Public Path A: quick DE/UK/RU/EN, mobile-safe panel. */
  compact?: boolean;
}) {
  const { t, i18n } = useTranslation("common");
  const { autoDetect, uiLocale, assistantLocale, setAutoDetect, setAssistantLocale, applyUiLocale } =
    useLocale();
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const currentCode = (getLocaleDefinition(uiLocale)?.code ?? uiLocale).toUpperCase();

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
        setMoreOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        setMoreOpen(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  /** One path for every UI pick — turns off auto, syncs assistant, changes i18n. */
  function pickLanguage(code: UiLocale) {
    applyUiLocale(code);
    void i18n.changeLanguage(code);
    setOpen(false);
    setMoreOpen(false);
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex min-h-10 min-w-10 items-center justify-center gap-1 rounded-lg border border-genesis-border-subtle px-2.5 py-2 text-sm text-genesis-muted transition hover:border-genesis-accent/30 hover:text-white"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={t("language.title")}
      >
        <span aria-hidden>🌐</span>
        <span className="font-medium uppercase tracking-wide text-white/90">{currentCode}</span>
      </button>
      {open && (
        <div
          role="dialog"
          aria-label={t("language.title")}
          className={
            compact
              ? "fixed inset-x-3 top-[4.5rem] z-50 max-h-[min(80dvh,32rem)] overflow-y-auto rounded-xl border border-genesis-border bg-genesis-panel p-4 shadow-card sm:absolute sm:inset-x-auto sm:right-0 sm:top-auto sm:mt-2 sm:w-72 sm:max-h-[min(70vh,28rem)]"
              : "absolute right-0 z-30 mt-2 w-[min(20rem,calc(100vw-1.5rem))] max-h-[min(70vh,28rem)] overflow-y-auto rounded-xl border border-genesis-border bg-genesis-panel p-4 shadow-card"
          }
        >
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-genesis-muted">
            {t("language.title")}
          </p>

          {compact ? (
            <>
              <label className="mb-3 flex cursor-pointer items-start gap-2 text-sm text-genesis-text">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={autoDetect}
                  onChange={(e) => setAutoDetect(e.target.checked)}
                />
                <span>{t("language.auto")}</span>
              </label>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {PUBLIC_QUICK.map((code) => {
                  const def = getLocaleDefinition(code);
                  const active = !autoDetect && uiLocale === code;
                  return (
                    <button
                      key={code}
                      type="button"
                      onClick={() => pickLanguage(code)}
                      className={`rounded-lg border px-2 py-2.5 text-center text-sm transition ${
                        active
                          ? "border-genesis-accent/50 bg-genesis-accent/15 text-white"
                          : "border-genesis-border-subtle text-genesis-text hover:border-genesis-accent/30"
                      }`}
                    >
                      <span className="block text-[10px] uppercase text-genesis-muted">{code}</span>
                      <span className="font-medium leading-tight">
                        {def?.nativeName ?? code}
                      </span>
                    </button>
                  );
                })}
              </div>
              <button
                type="button"
                className="mt-3 w-full rounded-lg border border-genesis-border-subtle px-3 py-2 text-xs text-genesis-muted hover:text-white"
                onClick={() => setMoreOpen((v) => !v)}
                aria-expanded={moreOpen}
              >
                {moreOpen ? t("language.less") : t("language.more")}
              </button>
              {moreOpen ? (
                <div className="mt-3 border-t border-genesis-border-subtle pt-3">
                  <LocaleSearchList
                    label={t("language.ui")}
                    value={uiLocale}
                    translatedOnly
                    onPick={pickLanguage}
                  />
                  <p className="mt-2 text-[10px] leading-relaxed text-genesis-muted">
                    {t("language.fullPackNote")}
                  </p>
                </div>
              ) : null}
            </>
          ) : (
            <>
              <label className="mb-4 flex cursor-pointer items-start gap-2 text-sm text-genesis-text">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={autoDetect}
                  onChange={(e) => setAutoDetect(e.target.checked)}
                />
                <span>{t("language.auto")}</span>
              </label>
              <LocaleSearchList
                label={t("language.ui")}
                value={uiLocale}
                onPick={pickLanguage}
              />
              <LocaleSearchList
                label={t("language.assistant")}
                value={assistantLocale}
                onPick={(code: AssistantLocale) => {
                  setAssistantLocale(code);
                  setOpen(false);
                }}
              />
              <p className="mt-1 text-[10px] leading-relaxed text-genesis-muted">
                {t("language.fallbackNote")}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
