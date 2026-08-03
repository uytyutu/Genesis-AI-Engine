"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import { StorefrontAtmosphere } from "./storefront/StorefrontAtmosphere";

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
    match: (p: string) => p.startsWith("/client/products"),
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

  return (
    <div className="storefront relative isolate min-h-screen overflow-x-hidden">
      <StorefrontAtmosphere />
      <div className="relative z-10 mx-auto min-h-screen max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
        <header className="border-b border-white/10 pb-5">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-genesis-accent">
            {BRAND_NAME} · AI Business Platform · Client
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-2 max-w-2xl text-sm text-zinc-400">{subtitle}</p>
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
