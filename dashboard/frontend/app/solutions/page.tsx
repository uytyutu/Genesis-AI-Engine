"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PublicPageShell } from "../components/PublicPageShell";
import {
  STORE_SOLUTION_CHIPS,
  WEBSITE_SOLUTION_CHIPS,
  LANDING_PACKAGES_EUR,
} from "../lib/commercialCatalog";

type CatalogGroup = {
  id: string;
  title: string;
  blurb: string;
  items: {
    id: string;
    label: string;
    niche_id: string;
    blurb: string;
    available: boolean;
    order_href: string | null;
  }[];
};

export default function SolutionsPage() {
  const [groups, setGroups] = useState<CatalogGroup[]>([]);
  const [modes, setModes] = useState<
    { id: string; name: string; price_eur: number; monthly_eur: number; tagline: string }[]
  >([]);

  useEffect(() => {
    void fetch("/api/public/solution-catalog?locale=de")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        setGroups(Array.isArray(data.groups) ? data.groups : []);
        setModes(Array.isArray(data.commerce_packages) ? data.commerce_packages : []);
      })
      .catch(() => {
        /* fallback chips below */
      });
  }, []);

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-6xl space-y-12 px-4 py-12">
        <header className="space-y-3">
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-300/80">
            Digital Business Creator
          </p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            Ready digital solutions — not templates
          </h1>
          <p className="max-w-2xl text-zinc-400">
            Choose a business vertical. Virtus Core interviews the owner, builds the company
            identity, then generates the site. Packages: Basic · Business · Premium — same prices
            as on /site and /order.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-3">
          {(modes.length
            ? modes
            : [
                {
                  id: "basic",
                  name: "Website Basic",
                  price_eur: LANDING_PACKAGES_EUR.basic,
                  monthly_eur: 0,
                  tagline: "Fertige Website — ohne Virtus Workspace.",
                },
                {
                  id: "business",
                  name: "Website Business",
                  price_eur: LANDING_PACKAGES_EUR.business,
                  monthly_eur: 0,
                  tagline: "Website + Virtus Client Workspace.",
                },
                {
                  id: "premium",
                  name: "Website Premium",
                  price_eur: LANDING_PACKAGES_EUR.premium,
                  monthly_eur: 0,
                  tagline: "Workspace + Cinematic Experience (inkl.).",
                },
              ]
          ).map((m) => (
            <article
              key={m.id}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <h2 className="text-xl font-semibold text-white">{m.name}</h2>
              <p className="mt-1 text-sm text-zinc-400">{m.tagline}</p>
              <p className="mt-3 text-lg text-emerald-200">
                {m.price_eur} €
                {m.monthly_eur ? ` + ${m.monthly_eur} €/mo` : " one-time"}
              </p>
              <Link
                href={`/order?package=${m.id}`}
                className="mt-4 inline-flex rounded-full bg-white px-4 py-2 text-sm font-medium text-black"
              >
                Continue
              </Link>
            </article>
          ))}
        </section>

        {groups.length > 0
          ? groups.map((g) => (
              <section key={g.id} className="space-y-4">
                <div>
                  <h2 className="text-2xl font-semibold text-white">{g.title}</h2>
                  <p className="text-sm text-zinc-400">{g.blurb}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {g.items.map((item) =>
                    item.available && item.order_href ? (
                      <Link
                        key={item.id}
                        href={item.order_href}
                        className="rounded-full border border-white/15 bg-white/[0.04] px-3 py-1.5 text-sm text-zinc-200 hover:border-emerald-400/50 hover:text-white"
                        title={item.blurb}
                      >
                        {item.label}
                      </Link>
                    ) : (
                      <span
                        key={item.id}
                        className="rounded-full border border-white/10 px-3 py-1.5 text-sm text-zinc-500"
                      >
                        {item.label} · soon
                      </span>
                    ),
                  )}
                </div>
              </section>
            ))
          : (
              <>
                <section className="space-y-4">
                  <h2 className="text-2xl font-semibold text-white">Business websites</h2>
                  <div className="flex flex-wrap gap-2">
                    {WEBSITE_SOLUTION_CHIPS.map((c) => (
                      <Link
                        key={c.id}
                        href={`/order?niche=${c.niche}&solution=${c.id}&package=business`}
                        className="rounded-full border border-white/15 bg-white/[0.04] px-3 py-1.5 text-sm text-zinc-200"
                      >
                        {c.label}
                      </Link>
                    ))}
                  </div>
                </section>
                <section className="space-y-4">
                  <h2 className="text-2xl font-semibold text-white">Online stores</h2>
                  <div className="flex flex-wrap gap-2">
                    {STORE_SOLUTION_CHIPS.map((c) => (
                      <Link
                        key={c.id}
                        href={`/order/shop?niche=${c.id}`}
                        className="rounded-full border border-white/15 bg-white/[0.04] px-3 py-1.5 text-sm text-zinc-200"
                      >
                        {c.label}
                      </Link>
                    ))}
                  </div>
                </section>
              </>
            )}
      </main>
    </PublicPageShell>
  );
}
