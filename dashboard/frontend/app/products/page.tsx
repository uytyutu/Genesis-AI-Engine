"use client";

import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { Badge, ButtonLink, Card } from "../components/ui";
import {
  COMMERCIAL_CATALOG,
  PRODUCT_SHOWCASE_GROUPS,
  type CommercialRow,
} from "../lib/commercialCatalog";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * G2.X — Product showcase: Websites · AI Bots · Website Services.
 * Guest can Order any available service; Coming Soon only for unfinished channels.
 */

function ProductCard({ row }: { row: CommercialRow }) {
  const live = row.cta !== "coming_soon";
  return (
    <Card
      padding="lg"
      className={`h-full text-left ${live ? "border-emerald-500/25" : "opacity-90"}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-lg font-semibold text-white">{row.name}</p>
          <p className="mt-1 text-sm font-medium text-emerald-200/90">
            {row.price_label}
          </p>
          <p className="mt-2 text-sm text-genesis-muted">{row.includes}</p>
        </div>
        <Badge variant={live ? "success" : "outline"}>{row.cta_label}</Badge>
      </div>
      {live && row.cta_href ? (
        <ButtonLink
          href={row.cta_href}
          variant="success"
          size="md"
          className="mt-4"
        >
          {row.cta_label} →
        </ButtonLink>
      ) : (
        <p className="mt-4 text-xs text-zinc-500">
          Not for sale yet — we only sell channels that already deliver.
        </p>
      )}
    </Card>
  );
}

export default function ProductsPage() {
  return (
    <PublicPageShell>
      <div className="mx-auto max-w-5xl py-4">
        <div className="text-center">
          <Badge variant="outline">{BRAND_NAME}</Badge>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Product catalog
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-genesis-muted">
            Buy one service or grow a project over time. No account required to
            order — register only if you want a personal office.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Link
              href="/order"
              className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
            >
              Order without account
            </Link>
            <Link
              href="/client/register"
              className="rounded-xl border border-white/20 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/5"
            >
              Create office account
            </Link>
          </div>
        </div>

        {PRODUCT_SHOWCASE_GROUPS.map((group) => {
          const rows = COMMERCIAL_CATALOG.filter((r) => r.group === group.id);
          if (rows.length === 0) return null;
          return (
            <section key={group.id} className="mt-12">
              <h2 className="text-2xl font-semibold text-white">{group.title}</h2>
              <p className="mt-1 text-sm text-genesis-muted">{group.blurb}</p>
              <ul className="mt-5 grid gap-4 sm:grid-cols-2">
                {rows.map((row) => (
                  <li key={row.id}>
                    <ProductCard row={row} />
                  </li>
                ))}
              </ul>
            </section>
          );
        })}

        <section className="mt-12 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
          <h2 className="text-lg font-semibold text-white">Two ways to buy</h2>
          <ul className="mt-3 space-y-2 text-sm text-zinc-300">
            <li>
              <strong className="text-white">One service</strong> — order Landing,
              SEO, Repair, or a bot as a guest. Done when delivered.
            </li>
            <li>
              <strong className="text-white">Virtus Core office</strong> — register,
              then expand the same project: add bot, SEO, speed, security later.
            </li>
          </ul>
        </section>

        <p className="mt-8 text-center text-sm text-genesis-muted">
          <Link href="/site" className="text-emerald-300 hover:underline">
            ← Back to {BRAND_NAME}
          </Link>
        </p>
      </div>
    </PublicPageShell>
  );
}
