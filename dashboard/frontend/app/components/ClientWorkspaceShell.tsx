"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

export const CLIENT_WORKSPACE_LINKS = [
  { href: "/client", label: "Dashboard", match: (p: string) => p === "/client" },
  {
    href: "/client/products",
    label: "My Products",
    match: (p: string) => p.startsWith("/client/products"),
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
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-6 sm:px-6 sm:py-8">
      <header className="border-b border-white/10 pb-5">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-300/90">
          {BRAND_NAME} · Client
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
                className={`rounded-lg px-3 py-1.5 text-sm ${
                  active
                    ? "bg-emerald-500/20 text-emerald-100"
                    : "text-zinc-400 hover:bg-white/5 hover:text-white"
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
  );
}
