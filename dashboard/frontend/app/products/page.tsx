"use client";

import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { ServiceCatalogGrid } from "../components/ServiceCatalogCards";
import { BotChannelIconRow } from "../components/ChannelBrandIcons";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * G2.X — Product showcase with service cards (form → pay).
 */

export default function ProductsPage() {
  return (
    <PublicPageShell>
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10">
        <header className="max-w-2xl space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/90">
            {BRAND_NAME}
          </p>
          <h1 className="text-3xl font-bold text-white sm:text-4xl">Products & services</h1>
          <p className="text-sm text-zinc-400 sm:text-base">
            Choose a card → fill the order form for that product → then pay. Coming Soon cards
            are honest: not for checkout until delivery is ready.
          </p>
          <BotChannelIconRow className="pt-1" />
        </header>

        <ServiceCatalogGrid mode="all" />

        <p className="text-center text-sm text-zinc-500">
          Need advice?{" "}
          <Link href="/site?view=vector" className="text-emerald-300 hover:underline">
            Ask Vector
          </Link>{" "}
          — he links you to the right form.
        </p>
      </div>
    </PublicPageShell>
  );
}
