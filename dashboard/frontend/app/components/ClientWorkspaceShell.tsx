"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useLocale } from "../context/LocaleContext";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import {
  lockedConnectedTeasers,
  resolveBccLocationTrail,
  type CommerceMode,
} from "../lib/workspaceNav";
import { BccLocationTrail } from "../lib/clientUi";
import { workspaceCopy, workspaceUiLang } from "../lib/workspaceCopy";
import type { UiLocale } from "../lib/locale/types";
import { usePathname } from "next/navigation";

const THEME_KEY = "virtus_client_theme_v1";
const BG_KEY = "virtus_client_bg_v1";
const MODE_KEY = "virtus_client_commerce_mode_v1";

export type ClientThemeId = "virtus_dark" | "storefront_light" | "graphite";

const THEMES: {
  id: ClientThemeId;
  label: string;
  vars: Record<string, string>;
  shellClass: string;
  shellBg: string;
}[] = [
  {
    id: "virtus_dark",
    label: "Virtus Dark",
    vars: {
      "--client-panel": "rgba(255,255,255,0.04)",
      "--client-border": "rgba(139,92,246,0.22)",
      "--client-text": "#f4f4f5",
      "--client-muted": "#a1a1aa",
    },
    shellClass: "text-zinc-100",
    shellBg: "#050508",
  },
  {
    id: "storefront_light",
    label: "Storefront Light",
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
    label: "Graphite",
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

function readTheme(): ClientThemeId {
  if (typeof window === "undefined") return "virtus_dark";
  const v = window.localStorage.getItem(THEME_KEY);
  if (v === "storefront_light" || v === "graphite" || v === "virtus_dark") return v;
  return "virtus_dark";
}

function readBg(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(BG_KEY) || "";
}

function readMode(): CommerceMode {
  if (typeof window === "undefined") return "standalone";
  const v = window.localStorage.getItem(MODE_KEY);
  return v === "connected" ? "connected" : "standalone";
}

/**
 * Inner page chrome for /client hubs.
 * Navigation lives in AppShell (sidebar + mobile tabs) — single BCC chrome.
 */
export function ClientWorkspaceShell({
  children,
  title,
  subtitle,
  commerceMode,
  hasStore: _hasStore,
  ecosystem,
  /** Dashboard: trail + micro-label only — page owns the H1 greeting. */
  compactChrome = false,
}: {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  commerceMode?: CommerceMode | string | null;
  hasStore?: boolean;
  ecosystem?: boolean;
  compactChrome?: boolean;
}) {
  void _hasStore;
  const pathname = usePathname() ?? "/client";
  const trail = resolveBccLocationTrail(pathname);
  const { uiLocale, applyUiLocale } = useLocale();
  const copy = workspaceCopy(workspaceUiLang(uiLocale));
  const [themeId, setThemeId] = useState<ClientThemeId>("virtus_dark");
  const [bgUrl, setBgUrl] = useState("");
  const [prefsOpen, setPrefsOpen] = useState(false);
  const [localMode, setLocalMode] = useState<CommerceMode>("standalone");

  useEffect(() => {
    setThemeId(readTheme());
    setBgUrl(readBg());
    setLocalMode(readMode());
  }, []);

  const mode = (commerceMode as CommerceMode) || localMode;
  const eco = ecosystem ?? mode === "connected";
  const locked = !eco ? lockedConnectedTeasers() : [];
  const theme = THEMES.find((t) => t.id === themeId) || THEMES[0];

  useEffect(() => {
    const root = document.documentElement;
    Object.entries(theme.vars).forEach(([k, v]) => root.style.setProperty(k, v));
  }, [theme]);

  function applyTheme(id: ClientThemeId) {
    setThemeId(id);
    window.localStorage.setItem(THEME_KEY, id);
  }

  function applyBg(url: string) {
    const next = url.trim();
    setBgUrl(next);
    if (next) window.localStorage.setItem(BG_KEY, next);
    else window.localStorage.removeItem(BG_KEY);
  }

  function applyMode(m: CommerceMode) {
    setLocalMode(m);
    window.localStorage.setItem(MODE_KEY, m);
  }

  return (
    <div
      className={`relative isolate min-h-full overflow-x-hidden ${theme.shellClass}`}
      data-client-workspace-shell="1"
      style={
        bgUrl
          ? {
              backgroundColor: theme.shellBg,
              backgroundImage: `linear-gradient(rgba(5,5,8,0.78), rgba(5,5,8,0.92)), url(${bgUrl})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }
          : { backgroundColor: theme.shellBg }
      }
    >
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(124,58,237,0.09),transparent_58%)]"
        aria-hidden
      />
      <div className="relative z-10 mx-auto min-h-full max-w-5xl overflow-x-hidden px-4 py-4 sm:px-6 sm:py-8 md:py-6">
        <header className="border-b border-violet-500/12 pb-4 sm:pb-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              {compactChrome ? (
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-violet-300/70">
                  {eco ? copy.connected : copy.standalone}
                </p>
              ) : (
                <>
                  <BccLocationTrail crumbs={trail} className="mb-2" />
                  <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-violet-300/75">
                    {BRAND_NAME} · {copy.brandLine} ·{" "}
                    {eco ? copy.connected : copy.standalone}
                  </p>
                  <h1 className="mt-2 text-xl font-semibold tracking-tight text-white sm:text-3xl">
                    {title}
                  </h1>
                  {subtitle ? (
                    <p className="mt-2 max-w-2xl text-sm text-zinc-400">{subtitle}</p>
                  ) : null}
                </>
              )}
            </div>
            <button
              type="button"
              onClick={() => setPrefsOpen((v) => !v)}
              className="shrink-0 rounded-xl border border-white/15 bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-300 hover:border-violet-400/40 hover:bg-violet-500/10"
            >
              {copy.themePrefs}
            </button>
          </div>
          {prefsOpen ? (
            <div className="mt-4 rounded-2xl border border-violet-500/20 bg-black/40 p-4 backdrop-blur-sm">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                {copy.language}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
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
                    onClick={() => applyUiLocale(code as UiLocale)}
                    className={`rounded-lg px-3 py-1.5 text-sm ${
                      workspaceUiLang(uiLocale) === code
                        ? "border border-violet-400/40 bg-violet-500/15 text-white"
                        : "border border-white/10 text-zinc-400 hover:bg-white/5"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                {copy.modePreview}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(["standalone", "connected"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => applyMode(m)}
                    className={`rounded-lg px-3 py-1.5 text-sm ${
                      mode === m
                        ? "border border-violet-400/40 bg-violet-500/15 text-white"
                        : "border border-white/10 text-zinc-400 hover:bg-white/5"
                    }`}
                  >
                    {m === "standalone" ? copy.standalone : copy.connected}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Design
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {THEMES.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => applyTheme(t.id)}
                    className={`rounded-lg px-3 py-1.5 text-sm ${
                      themeId === t.id
                        ? "border border-violet-400/40 bg-violet-500/15 text-white"
                        : "border border-white/10 text-zinc-400 hover:bg-white/5"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Hintergrund-URL
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <input
                  type="url"
                  value={bgUrl}
                  onChange={(e) => setBgUrl(e.target.value)}
                  placeholder="https://…/background.jpg"
                  className="min-w-0 flex-1 rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-sm text-white"
                />
                <button
                  type="button"
                  onClick={() => applyBg(bgUrl)}
                  className="rounded-xl bg-violet-600 px-3 py-2 text-sm font-semibold text-white"
                >
                  Übernehmen
                </button>
                <button
                  type="button"
                  onClick={() => applyBg("")}
                  className="rounded-xl border border-white/15 px-3 py-2 text-sm text-zinc-300"
                >
                  Löschen
                </button>
              </div>
            </div>
          ) : null}
          {locked.length ? (
            <p className="mt-3 text-xs text-zinc-500">
              Connected: {locked.map((l) => l.label).join(" · ")} —{" "}
              <Link href="/client/shop" className="text-violet-300/90 underline">
                Marketplace
              </Link>
            </p>
          ) : null}
          <p className="mt-2 text-[11px] text-zinc-600">
            {ASSISTANT_NAME} · nur gekaufte Produkte · eine Steuerung
          </p>
        </header>
        <main id="main-content" className="py-4 sm:py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
