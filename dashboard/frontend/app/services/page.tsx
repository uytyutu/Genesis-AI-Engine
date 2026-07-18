"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { PublicPageShell } from "../components/PublicPageShell";
import { PublicFunnelFooter } from "../components/navigation/PublicFunnelFooter";
import { PublicPageHero } from "../components/PublicPageHero";
import { Badge, ButtonLink, Card } from "../components/ui";
import {
  fetchPricingDisplay,
  logPricingEvent,
  type PricingDisplay,
  type ServiceCatalogItem,
  type ServiceCategory,
} from "../lib/pricingApi";
import { BRAND_NAME } from "../lib/publicBrand";

type GoToMarket = {
  levels?: { id: string; title: string; body: string }[];
  niches?: { id: string; label: string; examples: string }[];
  signals?: { signal: string; offer: string }[];
  modes?: { auto?: string; expert?: string };
};

function CatalogItemCard({ item }: { item: ServiceCatalogItem }) {
  const href = item.cta_href;
  const available = item.available;
  const tier = item.tier || (available ? "checkout" : "horizon");
  const isQuote = tier === "pilot_quote" || (!available && Boolean(href?.startsWith("mailto:")));

  const ctaClass = available
    ? "bg-genesis-accent text-white shadow-glow hover:brightness-110"
    : "border border-genesis-border-subtle text-genesis-muted hover:text-white";

  const badge = available ? (
    <Badge variant="success">Auto · Checkout</Badge>
  ) : isQuote ? (
    <Badge variant="outline">Expert · Anfrage</Badge>
  ) : (
    <Badge variant="outline">Horizon</Badge>
  );

  return (
    <Card
      glow={available}
      className={`relative flex flex-col ${
        available ? "border-emerald-500/35 bg-gradient-to-br from-emerald-950/20 to-genesis-panel" : ""
      }`}
      padding="lg"
    >
      <div className="absolute right-4 top-4">{badge}</div>
      <h3 className="pr-32 text-lg font-semibold">{item.name}</h3>
      <p className="mt-2 text-2xl font-bold text-genesis-accent">{item.price_label}</p>
      {item.timeline && (
        <p className="mt-1 text-xs text-genesis-muted">Frist: {item.timeline}</p>
      )}
      <p className="mt-3 flex-1 text-sm text-genesis-muted">{item.description}</p>
      {item.includes && item.includes.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-genesis-muted">
          {item.includes.map((x) => (
            <li key={x}>✓ {x}</li>
          ))}
        </ul>
      )}
      {href.startsWith("mailto:") ? (
        <a
          href={href}
          onClick={() => logPricingEvent("service_cta", item.id, "services")}
          className={`mt-5 inline-flex items-center justify-center rounded-xl px-5 py-2.5 text-sm font-semibold transition-smooth ${ctaClass}`}
        >
          {item.cta}
        </a>
      ) : (
        <ButtonLink
          href={href}
          variant={available ? "primary" : "secondary"}
          size="md"
          className="mt-5"
          onClick={() => logPricingEvent("service_cta", item.id, "services")}
        >
          {item.cta}
        </ButtonLink>
      )}
    </Card>
  );
}

function pickCategories(data: PricingDisplay | null): ServiceCategory[] {
  const raw = data?.service_categories?.length
    ? data.service_categories
    : data?.services?.length
      ? [
          {
            id: "legacy",
            name: "Services",
            description: "",
            items: data.services.map((s) => ({
              ...s,
              timeline: undefined,
              includes: undefined,
            })),
          },
        ]
      : [];

  const preferred = ["path_a_packages", "path_a_pilot", "horizon_agency"];
  const ordered = [
    ...preferred.map((id) => raw.find((c) => c.id === id)).filter(Boolean),
    ...raw.filter((c) => !preferred.includes(c.id)),
  ] as ServiceCategory[];

  return ordered
    .map((cat) => ({
      ...cat,
      items: cat.items.filter((item) => {
        if (cat.id === "path_a_packages" || cat.id === "path_a_pilot" || cat.id === "horizon_agency") {
          return true;
        }
        // Hide noisy legacy one-time rows — catalog is Path A + Pilot + Horizon
        return false;
      }),
    }))
    .filter((cat) => cat.items.length > 0);
}

export default function ServicesPage() {
  const [data, setData] = useState<PricingDisplay | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPricingDisplay().then((d) => {
      setData(d);
      setLoading(false);
    });
    logPricingEvent("page_view", null, "services");
  }, []);

  const categories = useMemo(() => pickCategories(data), [data]);
  const gtm = (data as PricingDisplay & { go_to_market?: GoToMarket })?.go_to_market;

  return (
    <PublicPageShell>
      <PublicPageHero
        badge="Digitale Präsenz für DE-SMB"
        badgeVariant="success"
        title={`Leistungen · ${BRAND_NAME}`}
        description="Wir prüfen die digitale Lücke und schlagen die passende Leistung vor — nicht „kaufen Sie irgendeine Website“."
      >
        <ButtonLink href="/order" variant="success" size="lg">
          Landing bestellen →
        </ButtonLink>
        <ButtonLink href="/site" variant="primary" size="lg" className="ml-2">
          Vector →
        </ButtonLink>
      </PublicPageHero>

      <section className="mt-10 grid gap-3 sm:grid-cols-3">
        {(gtm?.levels ?? [
          {
            id: "1",
            title: "1 · Produkt",
            body: "Landing Neustart — Checkout online.",
          },
          {
            id: "2",
            title: "2 · Zielgruppen",
            body: "Handwerk, Reparatur, Auto, Gesundheit, Beauty…",
          },
          {
            id: "3",
            title: "3 · Lead = Firma + Problem",
            body: "Signal → passende Leistung (Auto oder Anfrage).",
          },
        ]).map((level) => (
          <Card key={level.id} padding="md" className="border-white/10 bg-black/20">
            <p className="text-xs uppercase tracking-wide text-emerald-300/80">{level.title}</p>
            <p className="mt-2 text-sm text-genesis-muted">{level.body}</p>
          </Card>
        ))}
      </section>

      <section className="mt-8 grid gap-3 sm:grid-cols-2">
        <Card padding="md" className="border-emerald-500/25 bg-emerald-950/20">
          <Badge variant="success">Auto</Badge>
          <p className="mt-2 text-sm font-medium text-white">
            {gtm?.modes?.auto ?? "Landing — online Checkout"}
          </p>
          <p className="mt-1 text-xs text-genesis-muted">
            /order → Zahlung → Factory → ZIP. Anker-Umsatz.
          </p>
        </Card>
        <Card padding="md" className="border-sky-500/25 bg-sky-950/20">
          <Badge variant="outline">Expert</Badge>
          <p className="mt-2 text-sm font-medium text-white">
            {gtm?.modes?.expert ?? "Pilot — Anfrage"}
          </p>
          <p className="mt-1 text-xs text-genesis-muted">
            Site Boost, Audits, Migration… — Nachfrage-Radar für das nächste Auto-Produkt.
          </p>
        </Card>
      </section>

      {loading && categories.length === 0 && (
        <p className="mt-8 text-sm text-genesis-muted">Katalog wird geladen…</p>
      )}

      {categories.map((cat) => (
        <section key={cat.id} className="mt-12">
          <h2 className="text-xl font-bold">{cat.name}</h2>
          {cat.description && (
            <p className="mt-2 max-w-2xl text-sm text-genesis-muted">{cat.description}</p>
          )}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {cat.items.map((item) => (
              <CatalogItemCard key={item.id} item={item} />
            ))}
          </div>
        </section>
      ))}

      <section className="mt-16">
        <h2 className="text-xl font-bold">Zielgruppen (Pilot-Fokus)</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Branchen, in denen die Website Anrufe und Anfragen bringt.
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(gtm?.niches ?? []).map((n) => (
            <Card key={n.id} padding="md" className="border-white/10">
              <p className="font-semibold text-white">{n.label}</p>
              <p className="mt-1 text-xs text-genesis-muted">{n.examples}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-16">
        <h2 className="text-xl font-bold">Signal → Angebot</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Lead ist Firma + Problem. So bleibt der Dialog adressgenau.
        </p>
        <div className="mt-6 overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/5 text-xs uppercase tracking-wide text-genesis-muted">
              <tr>
                <th className="px-4 py-3">Signal</th>
                <th className="px-4 py-3">Leistung</th>
              </tr>
            </thead>
            <tbody>
              {(gtm?.signals ?? []).map((row) => (
                <tr key={row.signal} className="border-t border-white/5">
                  <td className="px-4 py-3 text-white/90">{row.signal}</td>
                  <td className="px-4 py-3 text-genesis-muted">{row.offer}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <Card className="mt-12 text-center" padding="md">
        <p className="text-sm text-genesis-muted">
          Nächstes Auto-Produkt = was Kunden nach dem Landing wirklich nachfragen (oft Site Boost) —
          nicht die längste Wunschliste.
        </p>
        <p className="mt-3 text-xs text-genesis-muted/80">
          Später (nach Pilot): nicht nur Technik-Lücken, sondern Ereignisse — neu eröffnet, Umzug,
          neue Leistungen, viele Reviews, Rebrand. Heute bewusst nicht verkauft.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <ButtonLink href="/order" variant="success" size="sm">
            Landing →
          </ButtonLink>
          <ButtonLink href="/kontakt" variant="secondary" size="sm">
            Anfrage →
          </ButtonLink>
        </div>
      </Card>
      <Suspense fallback={null}>
        <PublicFunnelFooter />
      </Suspense>
    </PublicPageShell>
  );
}
