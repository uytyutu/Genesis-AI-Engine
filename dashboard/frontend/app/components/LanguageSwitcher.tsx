"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useLocale } from "../context/LocaleContext";
import type { AssistantLocale, UiLocale } from "../lib/locale/types";

const UI_OPTIONS: UiLocale[] = ["ru", "en", "de"];

export function LanguageSwitcher() {
  const { t } = useTranslation("common");
  const { autoDetect, uiLocale, assistantLocale, setAutoDetect, setUiLocale, setAssistantLocale } =
    useLocale();
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

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
        🌐 {t(`language.${uiLocale}`)}
      </button>
      {open && (
        <div
          role="dialog"
          aria-label={t("language.title")}
          className="absolute right-0 z-30 mt-2 w-72 rounded-xl border border-genesis-border bg-genesis-panel p-4 shadow-card"
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
          <label className="mb-2 block text-xs text-genesis-muted">{t("language.ui")}</label>
          <select
            className="mb-3 w-full rounded-lg border border-genesis-border-subtle bg-genesis-bg px-3 py-2 text-sm text-white"
            value={uiLocale}
            disabled={autoDetect}
            onChange={(e) => setUiLocale(e.target.value as UiLocale)}
          >
            {UI_OPTIONS.map((code) => (
              <option key={code} value={code}>
                {t(`language.${code}`)}
              </option>
            ))}
          </select>
          <label className="mb-2 block text-xs text-genesis-muted">{t("language.assistant")}</label>
          <select
            className="w-full rounded-lg border border-genesis-border-subtle bg-genesis-bg px-3 py-2 text-sm text-white"
            value={assistantLocale}
            onChange={(e) => setAssistantLocale(e.target.value as AssistantLocale)}
          >
            {UI_OPTIONS.map((code) => (
              <option key={code} value={code}>
                {t(`language.${code}`)}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
