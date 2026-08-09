"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import {
  filterWorkspaceNav,
  lockedConnectedTeasers,
  type CommerceMode,
} from "../lib/workspaceNav";
import { StorefrontAtmosphere } from "./storefront/StorefrontAtmosphere";

const THEME_KEY = "virtus_client_theme_v1";
const BG_KEY = "virtus_client_bg_v1";
const MODE_KEY = "virtus_client_commerce_mode_v1";

export type ClientThemeId = "virtus_dark" | "storefront_light" | "graphite";

const THEMES: {
  id: ClientThemeId;
  label: string;
  vars: Record<string, string>;
  shellClass: string;
}[] = [
  {
    id: "virtus_dark",
    label: "Virtus Dark",
    vars: {
      "--client-panel": "rgba(255,255,255,0.03)",
      "--client-border": "rgba(255,255,255,0.1)",
      "--client-text": "#f4f4f5",
      "--client-muted": "#a1a1aa",
    },
    shellClass: "text-zinc-100",
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
  },
];

/** @deprecated use WORKSPACE_NAV / filterWorkspaceNav — kept for older imports */
export const CLIENT_WORKSPACE_LINKS = filterWorkspaceNav({
  commerceMode: "connected",
  hasStore: true,
  ecosystem: true,
}).map((i) => ({ href: i.href, label: i.label, match: i.match }));

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
  const pathname = usePathname() ?? "/client";
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

  const links = useMemo(
    () =>
      filterWorkspaceNav({
        commerceMode: mode,
        hasStore: hasStore ?? true,
        ecosystem: eco,
      }),
    [mode, hasStore, eco],
  );

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
      className={`storefront relative isolate min-h-screen overflow-x-hidden ${theme.shellClass}`}
      style={
        bgUrl
          ? {
              backgroundImage: `linear-gradient(rgba(9,9,11,0.72), rgba(9,9,11,0.88)), url(${bgUrl})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }
          : undefined
      }
    >
      {!bgUrl ? <StorefrontAtmosphere /> : null}
      <div className="relative z-10 mx-auto min-h-screen max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
        <header className="border-b border-white/10 pb-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-genesis-accent">
                {BRAND_NAME} · Virtus AI Workspace ·{" "}
                {eco ? "Connected" : "Standalone"}
              </p>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                {title}
              </h1>
              {subtitle ? (
                <p className="mt-2 max-w-2xl text-sm text-zinc-400">{subtitle}</p>
              ) : null}
            </div>
            <button
              type="button"
              onClick={() => setPrefsOpen((v) => !v)}
              className="rounded-xl border border-white/15 px-3 py-1.5 text-xs text-zinc-300 hover:bg-white/5"
            >
              Theme / режим
            </button>
          </div>
          {prefsOpen ? (
            <div className="mt-4 rounded-2xl border border-white/10 bg-black/30 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Режим Workspace (превью)
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(["standalone", "connected"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => applyMode(m)}
                    className={`rounded-lg px-3 py-1.5 text-sm capitalize ${
                      mode === m
                        ? "border border-emerald-400/40 bg-emerald-500/15 text-white"
                        : "border border-white/10 text-zinc-400 hover:bg-white/5"
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Тема кабинета
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {THEMES.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => applyTheme(t.id)}
                    className={`rounded-lg px-3 py-1.5 text-sm ${
                      themeId === t.id
                        ? "border border-emerald-400/40 bg-emerald-500/15 text-white"
                        : "border border-white/10 text-zinc-400 hover:bg-white/5"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Фон (URL изображения)
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <input
                  type="url"
                  value={bgUrl}
                  onChange={(e) => setBgUrl(e.target.value)}
                  placeholder="https://…/background.jpg"
                  className="min-w-[16rem] flex-1 rounded-xl border border-white/15 bg-black/40 px-3 py-2 text-sm text-white"
                />
                <button
                  type="button"
                  onClick={() => applyBg(bgUrl)}
                  className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                >
                  Apply
                </button>
                <button
                  type="button"
                  onClick={() => applyBg("")}
                  className="rounded-xl border border-white/15 px-3 py-2 text-sm text-zinc-300"
                >
                  Clear
                </button>
              </div>
            </div>
          ) : null}
          <nav
            className="mt-5 flex flex-wrap gap-2"
            aria-label="Virtus AI Workspace"
          >
            {links.map((link) => {
              const active = link.match(pathname);
              return (
                <Link
                  key={link.id}
                  href={link.href}
                  className={`rounded-lg px-3 py-1.5 text-sm transition ${
                    active
                      ? "border border-genesis-accent/40 bg-genesis-accent/15 text-white"
                      : "border border-transparent text-zinc-400 hover:border-white/10 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  {link.label}
                  {link.comingSoon ? (
                    <span className="ml-1 text-[10px] text-zinc-500">soon</span>
                  ) : null}
                </Link>
              );
            })}
          </nav>
          {locked.length ? (
            <p className="mt-3 text-xs text-zinc-500">
              Connected:{" "}
              {locked.map((l) => l.label).join(" · ")} —{" "}
              <Link href="/client/shop" className="text-emerald-300/90 underline">
                открыть в Marketplace
              </Link>
            </p>
          ) : null}
          <p className="mt-2 text-[11px] text-zinc-600">
            {ASSISTANT_NAME} управляет только купленными продуктами · одна панель
          </p>
        </header>
        <main id="main-content" className="py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
