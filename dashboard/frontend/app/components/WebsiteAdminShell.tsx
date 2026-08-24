"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";
import { BRAND_NAME } from "../lib/publicBrand";
import { BccLocationTrail } from "../lib/clientUi";
import { resolveBccLocationTrail } from "../lib/workspaceNav";

export type WebsiteAdminSectionId =
  | "dashboard"
  | "website"
  | "cinematic"
  | "design"
  | "media"
  | "files"
  | "support"
  | "ai"
  | "store"
  | "crm"
  | "automation"
  | "marketing"
  | "analytics";

const NAV: {
  id: WebsiteAdminSectionId;
  label: string;
  icon: string;
  ready: boolean;
}[] = [
  { id: "dashboard", label: "Übersicht", icon: "◈", ready: true },
  { id: "website", label: "Einstellungen", icon: "⚙", ready: true },
  { id: "cinematic", label: "Cinematic", icon: "▶", ready: true },
  { id: "design", label: "Design", icon: "◐", ready: true },
  { id: "media", label: "Medien", icon: "▦", ready: true },
  { id: "files", label: "Dateien", icon: "⇩", ready: true },
  { id: "support", label: "Support", icon: "✦", ready: true },
  { id: "ai", label: "KI-Assistent", icon: "◎", ready: true },
  { id: "store", label: "Shop", icon: "🛒", ready: false },
  { id: "crm", label: "CRM", icon: "◎", ready: false },
  { id: "automation", label: "Automation", icon: "⚡", ready: false },
  { id: "marketing", label: "Marketing", icon: "📣", ready: false },
  { id: "analytics", label: "Analytics", icon: "▣", ready: false },
];

type Props = {
  orderId: string;
  siteName: string;
  section: WebsiteAdminSectionId;
  onSection: (id: WebsiteAdminSectionId) => void;
  /** Standalone hides ecosystem modules; Connected shows Coming Soon. */
  commerceMode?: "standalone" | "connected" | string;
  vectorDock?: ReactNode;
  children: ReactNode;
};

export function WebsiteAdminComingSoon({ label }: { label: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-6 py-10 text-center">
      <p className="text-lg font-semibold text-white">{label}</p>
      <p className="mt-2 text-sm text-zinc-400">
        Coming with Virtus Core Connected — not included in Standalone Website.
      </p>
    </div>
  );
}

export function WebsiteAdminShell({
  orderId,
  siteName,
  section,
  onSection,
  commerceMode = "standalone",
  vectorDock,
  children,
}: Props) {
  const [navOpen, setNavOpen] = useState(false);
  // Always show Coming Soon modules (grey) — no fake Activate / Open.
  const navItems = NAV;

  return (
    <div className="min-h-screen bg-[#07070c] text-zinc-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_10%_-10%,rgba(16,185,129,0.12),transparent),radial-gradient(ellipse_60%_40%_at_90%_0%,rgba(99,102,241,0.1),transparent)] opacity-80" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-[1400px]">
        {navOpen ? (
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-30 bg-black/60 lg:hidden"
            onClick={() => setNavOpen(false)}
          />
        ) : null}

        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-[min(15.5rem,88vw)] flex-col border-r border-white/10 bg-[#0c0c12]/95 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 ${
            navOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="border-b border-white/10 px-4 py-5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-300/70">
              Website Control
            </p>
            <p className="mt-1 truncate text-sm font-semibold">{siteName}</p>
            <p className="mt-0.5 text-[11px] text-zinc-500">
              Website Control · {BRAND_NAME}
              {String(commerceMode || "").toLowerCase() === "connected"
                ? " · Connected"
                : " · Standalone"}
            </p>
          </div>

          <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
            {navItems.map((item) => {
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
                      ? "bg-emerald-500/15 text-emerald-100"
                      : item.ready
                        ? "text-zinc-300 hover:bg-white/5"
                        : "text-zinc-600 hover:bg-white/[0.03]"
                  }`}
                >
                  <span aria-hidden>{item.icon}</span>
                  <span className="flex-1">{item.label}</span>
                  {!item.ready ? (
                    <span className="text-[10px] uppercase tracking-wide text-zinc-600">
                      Soon
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>

          <div className="border-t border-white/10 p-3 text-xs">
            <Link
              href="/client/products"
              className="block rounded-lg px-2 py-2 text-zinc-400 hover:bg-white/5 hover:text-white"
            >
              ← Meine Produkte
            </Link>
            <p className="mt-1 px-2 text-[10px] text-zinc-600">Order {orderId}</p>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center gap-3 border-b border-white/10 px-4 py-3 lg:px-6">
            <button
              type="button"
              className="rounded-lg border border-white/10 px-2.5 py-1.5 text-sm lg:hidden"
              onClick={() => setNavOpen(true)}
            >
              Menu
            </button>
            <div className="min-w-0 flex-1">
              <BccLocationTrail
                crumbs={[
                  ...resolveBccLocationTrail(`/client/websites/${orderId}/admin`),
                  { label: NAV.find((n) => n.id === section)?.label || section },
                ]}
                className="mb-1"
              />
              <h1 className="truncate text-base font-semibold capitalize">
                {NAV.find((n) => n.id === section)?.label || section}
              </h1>
              <p className="text-[11px] text-zinc-500">
                Edit live — changes apply to your website preview
              </p>
            </div>
          </header>

          <main className="flex-1 px-4 py-5 lg:px-6">{children}</main>
        </div>

        {vectorDock}
      </div>
    </div>
  );
}
