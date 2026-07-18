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
  const isQuote = !available && Boolean(href?.startsWith("mailto:"));

  const ctaClass = available
    ? "bg-genesis-accent text-white shadow-glow hover:brightness-110"
    : "border border-genesis-border-subtle text-genesis-muted hover:text-white";

  const badge = available ? (
    <Badge variant="success">Online bestellen</Badge>
  ) : isQuote ? (
    <Badge variant="outline">Auf Anfrage</Badge>
  ) : (
    <Badge variant="outline">Bald</Badge>
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
      <h3 className="pr-36 text-lg font-semibold">{item.name}</h3>
      <p className="mt-2 text-2xl font-bold text-genesis-accent">{item.price_label}</p>
      {item.timeline && (
        <p className="mt-1 text-xs text-genesis-muted">Dauer: {item.timeline}</p>
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
            name: "Leistungen",
            description: "",
            items: data.services.map((s) => ({
              ...s,
              timeline: undefined,
              includes: undefined,
            })),
          },
        ]
      : [];

  // Prefer Path A catalog; fall back to legacy "website" while backend still serves truth-12.
  const preferred = ["path_a_packages", "path_a_pilot", "website"];
  const ordered = [
    ...preferred.map((id) => raw.find((c) => c.id === id)).filter(Boolean),
    ...raw.filter((c) => preferred.includes(c.id) === false && c.id !== "horizon_agency"),
  ] as ServiceCategory[];

  return ordered
    .map((cat) => ({
      ...cat,
      items: cat.items.filter((item) => {
        if (cat.id === "path_a_packages" || cat.id === "path_a_pilot") return true;
        if (cat.id === "website") return Boolean(item.available);
        // Quote/mailto pilots only; hide horizon / Bald vision rows from buyers.
        return Boolean(item.cta_href?.startsWith("mailto:"));
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
        badge="Für lokale Betriebe in Deutschland"
        badgeVariant="success"
        title={`Leistungen · ${BRAND_NAME}`}
        description="Wir helfen Ihnen zu einem klaren digitalen Auftritt — moderne Website, Kontakte und Weg zur Anfrage. Weitere Verbesserungen auf Anfrage."
      >
        <ButtonLink href="/order" variant="success" size="lg">
          Website bestellen →
        </ButtonLink>
        <ButtonLink href="/kontakt" variant="primary" size="lg" className="ml-2">
          Frage stellen →
        </ButtonLink>
      </PublicPageHero>

      <section className="mt-10 grid gap-3 sm:grid-cols-3">
        {(gtm?.levels ?? [
          {
            id: "1",
            title: "1 · Leistung",
            body: "Fertige Website für Ihren Betrieb.",
          },
          {
            id: "2",
            title: "2 · Für wen",
            body: "Handwerk, Auto, Gesundheit, Beauty und lokale Services.",
          },
          {
            id: "3",
            title: "3 · Passgenau",
            body: "Wir schauen, was fehlt — und schlagen die passende Lösung vor.",
          },
        ]).map((level) => (
          <Card key={level.id} padding="md" className="border-white/10 bg-black/20">
            <p className="text-xs uppercase tracking-wide text-emerald-300/80">{level.title}</p>
            <p className="mt-2 text-sm text-genesis-muted">{level.body}</p>
          </Card>
        ))}
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
        <h2 className="text-xl font-bold">Für wen geeignet</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Branchen, in denen Kunden online nach dem richtigen Betrieb suchen.
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
        <h2 className="text-xl font-bold">Typische Situationen</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Wenn etwas fehlt, gibt es oft eine passende Leistung.
        </p>
        <div className="mt-6 overflow-x-auto rounded-xl border border-white/10">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/5 text-xs uppercase tracking-wide text-genesis-muted">
              <tr>
                <th className="px-4 py-3">Situation</th>
                <th className="px-4 py-3">Mögliche Leistung</th>
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
          Fragen zu Bestellung oder Status? Schreiben Sie an hello@genesis-ai-engine.com — auf Deutsch.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <ButtonLink href="/order" variant="success" size="sm">
            Website bestellen →
          </ButtonLink>
          <ButtonLink href="/kontakt" variant="secondary" size="sm">
            Kontakt →
          </ButtonLink>
        </div>
      </Card>
      <Suspense fallback={null}>
        <PublicFunnelFooter />
      </Suspense>
    </PublicPageShell>
  );
}
