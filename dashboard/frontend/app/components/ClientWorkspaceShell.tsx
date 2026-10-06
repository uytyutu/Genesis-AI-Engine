"use client";

import { useEffect, useState } from "react";
import { useLocale } from "../context/LocaleContext";
import { BRAND_NAME } from "../lib/publicBrand";
import { filterWorkspaceNav, type CommerceMode } from "../lib/workspaceNav";
import { workspaceCopy, workspaceUiLang } from "../lib/workspaceCopy";
import type { UiLocale } from "../lib/locale/types";

const THEME_KEY = "virtus_client_theme_v1";
const MODE_KEY = "virtus_client_commerce_mode_v1";

export type ClientThemeId = "virtus_dark" | "storefront_light" | "graphite";

const THEMES: {
  id: ClientThemeId;
  vars: Record<string, string>;
  shellClass: string;
  shellBg: string;
}[] = [
  {
    id: "virtus_dark",
    vars: {
      "--client-panel": "rgba(255,255,255,0.03)",
      "--client-border": "rgba(255,255,255,0.1)",
      "--client-text": "#f4f4f5",
      "--client-muted": "#a1a1aa",
    },
    shellClass: "text-zinc-100",
    shellBg: "#050508",
  },
  {
    id: "storefront_light",
    vars: {
      "--client-panel": "rgba(255,255,255,0.72)",
      "--client-border": "rgba(15,23,42,0.12)",
      "--client-text": "#0f172a",
      "--client-muted": "#475569",
    },
    shellClass: "text-slate-900 [&_h1]:text-slate-900 [&_p]:text-slate-600",
    shellBg: "#f8fafc",
  },
  {
    id: "graphite",
    vars: {
      "--client-panel": "rgba(24,24,27,0.85)",
      "--client-border": "rgba(113,113,122,0.35)",
      "--client-text": "#e4e4e7",
      "--client-muted": "#a1a1aa",
    },
    shellClass: "text-zinc-200",
    shellBg: "#18181b",
  },
];

/** @deprecated use WORKSPACE_NAV / filterWorkspaceNav — kept for older imports */
export const CLIENT_WORKSPACE_LINKS = filterWorkspaceNav({
  commerceMode: "connected",
  hasStore: true,
  ecosystem: true,
  primaryOnly: true,
}).map((i) => ({ href: i.href, label: i.label, match: i.match }));

function readTheme(): ClientThemeId {
  if (typeof window === "undefined") return "virtus_dark";
  const v = window.localStorage.getItem(THEME_KEY);
  if (v === "storefront_light" || v === "graphite" || v === "virtus_dark") return v;
  return "virtus_dark";
}

function readMode(): CommerceMode {
  if (typeof window === "undefined") return "standalone";
  const v = window.localStorage.getItem(MODE_KEY);
  return v === "connected" ? "connected" : "standalone";
}

export function ClientWorkspaceShell({
  children,
  title,
  subtitle,
  commerceMode,
  hasStore,
  ecosystem,
}: {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  commerceMode?: CommerceMode | string | null;
  hasStore?: boolean;
  ecosystem?: boolean;
}) {
  const { uiLocale, applyUiLocale } = useLocale();
  const copy = workspaceCopy(workspaceUiLang(uiLocale));
  const [themeId, setThemeId] = useState<ClientThemeId>("virtus_dark");
  const [langOpen, setLangOpen] = useState(false);
  const [localMode] = useState<CommerceMode>("standalone");

  useEffect(() => {
    setThemeId(readTheme());
    void readMode();
  }, []);

  const mode = (commerceMode as CommerceMode) || localMode;
  const eco = ecosystem ?? mode === "connected";
  void hasStore;
  void eco;

  const theme = THEMES.find((t) => t.id === themeId) || THEMES[0];

  useEffect(() => {
    const root = document.documentElement;
    Object.entries(theme.vars).forEach(([k, v]) => root.style.setProperty(k, v));
  }, [theme]);

  return (
    <div
      className={`relative isolate min-h-full overflow-x-hidden ${theme.shellClass}`}
      data-client-workspace-shell="1"
      style={{ backgroundColor: theme.shellBg }}
    >
      <div className="relative z-10 mx-auto min-h-full max-w-5xl overflow-x-hidden px-4 py-4 sm:px-6 sm:py-8 md:py-6">
        <header className="border-b border-white/10 pb-4 sm:pb-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-emerald-300/90">
                {BRAND_NAME}
              </p>
              <h1 className="mt-2 text-xl font-semibold tracking-tight text-white sm:text-3xl">
                {title}
              </h1>
              {subtitle ? (
                <p className="mt-2 max-w-2xl text-sm text-zinc-400">{subtitle}</p>
              ) : (
                <p className="mt-2 max-w-2xl text-sm text-zinc-500">{copy.brandLine}</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => setLangOpen((v) => !v)}
              className="shrink-0 rounded-xl border border-white/15 px-3 py-1.5 text-xs text-zinc-300 hover:bg-white/5"
            >
              {copy.language}
            </button>
          </div>
          {langOpen ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {(
                [
                  ["de", "Deutsch"],
                  ["en", "English"],
                  ["ru", "Русский"],
                ] as const
              ).map(([code, label]) => (
                <button
                  key={code}
                  type="button"
                  onClick={() => {
                    applyUiLocale(code as UiLocale);
                    setLangOpen(false);
                  }}
                  className={`rounded-lg px-3 py-1.5 text-sm ${
                    workspaceUiLang(uiLocale) === code
                      ? "border border-emerald-400/40 bg-emerald-500/15 text-white"
                      : "border border-white/10 text-zinc-400 hover:bg-white/5"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          ) : null}
        </header>
        <main id="main-content" className="py-4 sm:py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
