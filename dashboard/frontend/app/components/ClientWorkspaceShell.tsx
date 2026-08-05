"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import { StorefrontAtmosphere } from "./storefront/StorefrontAtmosphere";

const THEME_KEY = "virtus_client_theme_v1";
const BG_KEY = "virtus_client_bg_v1";

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

export const CLIENT_WORKSPACE_LINKS = [
  { href: "/client", label: "Dashboard", match: (p: string) => p === "/client" },
  {
    href: "/client/onboarding",
    label: "Профиль",
    match: (p: string) => p.startsWith("/client/onboarding"),
  },
  {
    href: "/client/shop",
    label: "Магазин",
    match: (p: string) => p.startsWith("/client/shop"),
  },
  {
    href: "/client/products",
    label: "My Products",
    match: (p: string) =>
      p.startsWith("/client/products") || p.startsWith("/client/stores"),
  },
  {
    href: "/client/bots",
    label: "Боты",
    match: (p: string) => p.startsWith("/client/bots"),
  },
  {
    href: "/client/orders",
    label: "Orders",
    match: (p: string) => p.startsWith("/client/orders"),
  },
  {
    href: "/client/licenses",
    label: "Licenses",
    match: (p: string) => p.startsWith("/client/licenses"),
  },
  {
    href: "/client/billing",
    label: "Billing",
    match: (p: string) => p.startsWith("/client/billing"),
  },
  {
    href: "/client/analyses",
    label: "Analyses",
    match: (p: string) => p.startsWith("/client/analyses"),
  },
  {
    href: "/client/downloads",
    label: "Downloads",
    match: (p: string) => p.startsWith("/client/downloads"),
  },
  {
    href: "/client/support",
    label: "Support",
    match: (p: string) => p.startsWith("/client/support"),
  },
  {
    href: "/client/privacy",
    label: "Privacy & Cookies",
    match: (p: string) => p.startsWith("/client/privacy"),
  },
  {
    href: "/projects/chatbot",
    label: ASSISTANT_NAME,
    match: (p: string) => p.startsWith("/projects/chatbot"),
  },
] as const;

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

export function ClientWorkspaceShell({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}) {
  const pathname = usePathname() ?? "/client";
  const [themeId, setThemeId] = useState<ClientThemeId>("virtus_dark");
  const [bgUrl, setBgUrl] = useState("");
  const [prefsOpen, setPrefsOpen] = useState(false);

  useEffect(() => {
    setThemeId(readTheme());
    setBgUrl(readBg());
  }, []);

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
                {BRAND_NAME} · AI Business Platform · Client
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
              Theme / фон
            </button>
          </div>
          {prefsOpen ? (
            <div className="mt-4 rounded-2xl border border-white/10 bg-black/30 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
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
            aria-label="Client workspace"
          >
            {CLIENT_WORKSPACE_LINKS.map((link) => {
              const active = link.match(pathname);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-lg px-3 py-1.5 text-sm transition ${
                    active
                      ? "border border-genesis-accent/40 bg-genesis-accent/15 text-white"
                      : "border border-transparent text-zinc-400 hover:border-white/10 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </header>
        <main id="main-content" className="py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
