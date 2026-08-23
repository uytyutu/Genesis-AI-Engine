"use client";

import Link from "next/link";
import { StorefrontAtmosphere } from "./storefront/StorefrontAtmosphere";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * Auth surfaces (login / register) — same atmosphere as /site showcase,
 * not a bare formulary page.
 */
export function ClientAuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <>
      <StorefrontAtmosphere />
      <div className="storefront relative isolate min-h-screen overflow-x-hidden">
        <div className="relative z-10 mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-12">
          <Link
            href="/site"
            className="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-300/90 transition hover:text-emerald-200"
          >
            {BRAND_NAME}
          </Link>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {title}
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-zinc-400">{subtitle}</p>
          <div className="mt-8 rounded-2xl border border-white/10 bg-black/35 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur-md sm:p-6">
            {children}
          </div>
          {footer ? <div className="mt-6 space-y-3 text-sm text-zinc-400">{footer}</div> : null}
        </div>
      </div>
    </>
  );
}
