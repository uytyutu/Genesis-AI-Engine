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

function LocaleSearchList({
  label,
  value,
  disabled,
  onPick,
}: {
  label: string;
  value: UiLocale;
  disabled?: boolean;
  onPick: (code: UiLocale) => void;
}) {
  const { t } = useTranslation("common");
  const [query, setQuery] = useState("");

  const filtered = useMemo(
    () => LOCALE_REGISTRY.filter((def) => localeMatchesQuery(def, query)),
    [query],
  );

  return (
    <div className="mb-4 last:mb-0">
      <label className="mb-2 block text-xs text-genesis-muted">{label}</label>
      <input
        type="search"
        value={query}
        disabled={disabled}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={t("language.search")}
        className="mb-2 w-full rounded-lg border border-genesis-border-subtle bg-genesis-bg px-3 py-2 text-sm text-white placeholder:text-genesis-muted/60 disabled:opacity-50"
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
                  disabled={disabled}
                  onClick={() => onPick(def.code)}
                  className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition hover:bg-white/5 disabled:opacity-50 ${
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

export function LanguageSwitcher() {
  const { t } = useTranslation("common");
  const { autoDetect, uiLocale, assistantLocale, setAutoDetect, setUiLocale, setAssistantLocale } =
    useLocale();
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const currentLabel =
    getLocaleDefinition(uiLocale)?.nativeName ?? uiLocale;

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="rounded-lg border border-genesis-border-subtle px-3 py-2 text-sm text-genesis-muted transition hover:border-genesis-accent/30 hover:text-white"
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        🌐 {currentLabel}
      </button>
      {open && (
        <div
          role="dialog"
          aria-label={t("language.title")}
          className="absolute right-0 z-30 mt-2 w-80 rounded-xl border border-genesis-border bg-genesis-panel p-4 shadow-card"
        >
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-genesis-muted">
            {t("language.title")}
          </p>
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
            disabled={autoDetect}
            onPick={(code) => setUiLocale(code)}
          />
          <LocaleSearchList
            label={t("language.assistant")}
            value={assistantLocale}
            onPick={(code: AssistantLocale) => setAssistantLocale(code)}
          />
          <p className="mt-1 text-[10px] leading-relaxed text-genesis-muted">
            {t("language.fallbackNote")}
          </p>
        </div>
      )}
    </div>
  );
}
