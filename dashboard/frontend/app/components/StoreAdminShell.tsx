"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { BRAND_NAME } from "../lib/publicBrand";
import { publicApiBase } from "../lib/publicApiBase";

export type StoreAdminSectionId =
  | "dashboard"
  | "products"
  | "orders"
  | "customers"
  | "commerce"
  | "payments"
  | "shipping"
  | "email"
  | "integrations"
  | "contact"
  | "marketing"
  | "analytics"
  | "design"
  | "settings";

const NAV: { id: StoreAdminSectionId; label: string; icon: string; ready: boolean }[] = [
  { id: "dashboard", label: "Dashboard", icon: "◈", ready: true },
  { id: "products", label: "Products", icon: "▦", ready: true },
  { id: "orders", label: "Orders", icon: "☰", ready: true },
  { id: "customers", label: "Customers", icon: "◎", ready: true },
  { id: "commerce", label: "Commerce", icon: "⬡", ready: true },
  { id: "payments", label: "Payments", icon: "◇", ready: true },
  { id: "shipping", label: "Shipping", icon: "⇢", ready: true },
  { id: "email", label: "Email", icon: "✉", ready: true },
  { id: "integrations", label: "Integrations", icon: "⧉", ready: true },
  { id: "contact", label: "Contact", icon: "☎", ready: true },
  { id: "marketing", label: "Marketing", icon: "✦", ready: false },
  { id: "analytics", label: "Analytics", icon: "▣", ready: false },
  { id: "design", label: "Design", icon: "◐", ready: true },
  { id: "settings", label: "Settings", icon: "⚙", ready: false },
];

const THEME_KEY = "virtus_store_admin_theme_v1";
const API = publicApiBase();

type Props = {
  orderId: string;
  storeName: string;
  section: StoreAdminSectionId;
  onSection: (id: StoreAdminSectionId) => void;
  onThemeChange?: (theme: "dark" | "light") => void;
  /** Compact Vector readiness strip under the header */
  vectorStrip?: ReactNode;
  /** Docked Vector dialog (Phase 2) */
  vectorDock?: ReactNode;
  children: ReactNode;
};

export function StoreAdminShell({
  orderId,
  storeName,
  section,
  onSection,
  onThemeChange,
  vectorStrip,
  vectorDock,
  children,
}: Props) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY);
      if (saved === "light" || saved === "dark") {
        setTheme(saved);
        onThemeChange?.(saved);
      } else {
        onThemeChange?.("dark");
      }
    } catch {
      onThemeChange?.("dark");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- notify parent once on mount
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch {
        /* ignore */
      }
      onThemeChange?.(next);
      return next;
    });
  };

  const dark = theme === "dark";

  return (
    <div
      className={`min-h-screen transition-colors duration-300 ${
        dark
          ? "bg-[#07070c] text-zinc-100"
          : "bg-[#f4f1eb] text-slate-900"
      }`}
    >
      <div
        className={`pointer-events-none fixed inset-0 opacity-80 ${
          dark
            ? "bg-[radial-gradient(ellipse_80%_50%_at_10%_-10%,rgba(16,185,129,0.12),transparent),radial-gradient(ellipse_60%_40%_at_90%_0%,rgba(99,102,241,0.1),transparent)]"
            : "bg-[radial-gradient(ellipse_80%_50%_at_10%_-10%,rgba(16,185,129,0.08),transparent),radial-gradient(ellipse_60%_40%_at_90%_0%,rgba(245,158,11,0.08),transparent)]"
        }`}
      />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-[1400px]">
        {/* Mobile overlay */}
        {navOpen ? (
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-30 bg-black/50 lg:hidden"
            onClick={() => setNavOpen(false)}
          />
        ) : null}

        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-[15.5rem] flex-col border-r backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 ${
            navOpen ? "translate-x-0" : "-translate-x-full"
          } ${
            dark
              ? "border-white/10 bg-[#0c0c12]/95"
              : "border-slate-200/80 bg-white/90"
          }`}
        >
          <div className="border-b border-inherit px-4 py-5">
            <p
              className={`text-[10px] font-semibold uppercase tracking-[0.2em] ${
                dark ? "text-emerald-300/70" : "text-emerald-700/80"
              }`}
            >
              Store Admin
            </p>
            <p className="mt-1 truncate text-sm font-semibold">{storeName}</p>
            <p
              className={`mt-0.5 text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}
            >
              Not {BRAND_NAME} workspace · shop only
            </p>
          </div>

          <nav className="flex-1 space-y-0.5 overflow-y-auto p-3" aria-label="Store Admin">
            {NAV.map((item) => {
              const active = section === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    onSection(item.id);
                    setNavOpen(false);
                  }}
                  className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition ${
                    active
                      ? dark
                        ? "bg-emerald-500/20 text-emerald-100 ring-1 ring-emerald-400/30"
                        : "bg-emerald-500/15 text-emerald-900 ring-1 ring-emerald-600/25"
                      : dark
                        ? "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100"
                        : "text-slate-600 hover:bg-slate-900/[0.04] hover:text-slate-900"
                  }`}
                >
                  <span className="w-5 text-center opacity-80" aria-hidden>
                    {item.icon}
                  </span>
                  <span className="flex-1">{item.label}</span>
                  {!item.ready ? (
                    <span
                      className={`rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${
                        dark
                          ? "bg-white/5 text-zinc-500"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      Soon
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>

          <div className="space-y-2 border-t border-inherit p-3">
            <Link
              href={`/client/stores/${orderId}`}
              className={`block rounded-xl px-3 py-2 text-xs font-medium transition ${
                dark
                  ? "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100"
                  : "text-slate-600 hover:bg-slate-900/[0.04]"
              }`}
            >
              ← Back to Virtus product
            </Link>
            <Link
              href={`${API}/api/client/stores/${orderId}/live/`}
              target="_blank"
              rel="noreferrer"
              className={`block rounded-xl px-3 py-2 text-xs font-medium transition ${
                dark
                  ? "text-emerald-300/90 hover:bg-emerald-500/10"
                  : "text-emerald-800 hover:bg-emerald-500/10"
              }`}
            >
              Open live shop ↗
            </Link>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header
            className={`sticky top-0 z-20 flex items-center gap-3 border-b px-4 py-3 backdrop-blur-xl sm:px-6 ${
              dark
                ? "border-white/10 bg-[#07070c]/80"
                : "border-slate-200/80 bg-[#f4f1eb]/85"
            }`}
          >
            <button
              type="button"
              className={`rounded-xl p-2 lg:hidden ${
                dark ? "bg-white/5" : "bg-white shadow-sm"
              }`}
              aria-label="Open menu"
              onClick={() => setNavOpen(true)}
            >
              ☰
            </button>
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-lg font-semibold tracking-tight sm:text-xl">
                {NAV.find((n) => n.id === section)?.label || "Dashboard"}
              </h1>
              <p
                className={`truncate text-xs ${dark ? "text-zinc-500" : "text-slate-500"}`}
              >
                {storeName}
              </p>
            </div>
            <button
              type="button"
              onClick={toggleTheme}
              className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                dark
                  ? "border border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
                  : "border border-slate-200 bg-white shadow-sm hover:bg-slate-50"
              }`}
            >
              {dark ? "Light" : "Dark"}
            </button>
          </header>

          {vectorStrip ? (
            <div
              className={`px-4 py-2.5 sm:px-6 ${
                dark ? "border-b border-white/10" : "border-b border-slate-200/80"
              }`}
            >
              {vectorStrip}
            </div>
          ) : null}

          <main className="flex-1 p-4 sm:p-6 lg:p-8 pb-28 sm:pb-8">{children}</main>
          {vectorDock}
        </div>
      </div>
    </div>
  );
}

export function StoreAdminComingSoon({
  title,
  dark = true,
}: {
  title: string;
  dark?: boolean;
}) {
  return (
    <div
      className={`rounded-3xl border p-8 text-center sm:p-12 ${
        dark
          ? "border-white/10 bg-white/[0.03]"
          : "border-slate-200 bg-white/70 shadow-sm"
      }`}
    >
      <p
        className={`text-xs font-semibold uppercase tracking-[0.2em] ${
          dark ? "text-emerald-300/70" : "text-emerald-700"
        }`}
      >
        Coming next
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-tight">{title}</h2>
      <p
        className={`mx-auto mt-2 max-w-md text-sm ${
          dark ? "text-zinc-400" : "text-slate-600"
        }`}
      >
        This section opens in the next Store Admin release. The foundation is ready —
        product management and commerce follow step by step.
      </p>
    </div>
  );
}

export { NAV as STORE_ADMIN_NAV };
