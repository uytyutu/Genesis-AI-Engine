"use client";

import { useEffect, useState } from "react";
import { PublicPageShell } from "../components/PublicPageShell";
import { PublicPageHero } from "../components/PublicPageHero";
import { Badge, ButtonLink, Card } from "../components/ui";
import {
  fetchPricingDisplay,
  logPricingEvent,
  type BusinessUnit,
  type PricingDisplay,
  type ServiceCatalogItem,
  type ServiceCategory,
} from "../lib/pricingApi";

function CatalogItemCard({ item }: { item: ServiceCatalogItem }) {
  const href = item.cta_href;
  const available = item.available;

  const ctaClass = available
    ? "bg-genesis-accent text-white shadow-glow hover:brightness-110"
    : "border border-genesis-border-subtle text-genesis-muted hover:text-white";

  return (
    <Card
      glow={available}
      className={`relative flex flex-col ${
        available ? "border-emerald-500/35 bg-gradient-to-br from-emerald-950/20 to-genesis-panel" : ""
      }`}
      padding="lg"
    >
      {available ? (
        <div className="absolute right-4 top-4">
          <Badge variant="success">Заказ онлайн</Badge>
        </div>
      ) : (
        <div className="absolute right-4 top-4">
          <Badge variant="outline">По запросу</Badge>
        </div>
      )}
      <h3 className="pr-28 text-lg font-semibold">{item.name}</h3>
      <p className="mt-2 text-2xl font-bold text-genesis-accent">{item.price_label}</p>
      {item.timeline && (
        <p className="mt-1 text-xs text-genesis-muted">Срок: {item.timeline}</p>
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

function UnitCard({ unit }: { unit: BusinessUnit }) {
  return (
    <Card className="border-indigo-500/20 bg-gradient-to-br from-indigo-950/20 to-genesis-panel/80" padding="lg">
      <Badge variant="outline" className="border-indigo-400/30 text-indigo-200">
        Concept Preview
      </Badge>
      <p className="mt-3 text-lg font-bold">{unit.name}</p>
      <p className="mt-1 text-sm text-genesis-muted">{unit.tagline}</p>
      <ul className="mt-4 space-y-1.5 text-sm text-genesis-muted">
        {unit.includes.map((x) => (
          <li key={x}>· {x}</li>
        ))}
      </ul>
      <ButtonLink
        href={unit.cta_href}
        variant="secondary"
        size="sm"
        className="mt-4"
        onClick={() => logPricingEvent("unit_cta", unit.id, "services")}
      >
        Узнать о планах
      </ButtonLink>
    </Card>
  );
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

  const categories: ServiceCategory[] =
    data?.service_categories?.length
      ? data.service_categories
      : data?.services?.length
        ? [
            {
              id: "legacy",
              name: "Услуги",
              description: "",
              items: data.services.map((s) => ({
                ...s,
                timeline: undefined,
                includes: undefined,
              })),
            },
          ]
        : [];

  return (
    <PublicPageShell>
      <PublicPageHero
        badge="Результат под ключ"
        badgeVariant="success"
        title="Услуги Genesis"
        description="Готовый результат под ключ — сайт, бот, AI. Цена «от», срок и состав на карточке. Один проект — услуга; много проектов сами — Studio."
      >
        <ButtonLink href="/order" variant="success" size="lg">
          Заказать landing →
        </ButtonLink>
        <ButtonLink href="/products" variant="ghost" size="lg" className="ml-2">
          Или Genesis Studio
        </ButtonLink>
      </PublicPageHero>

      {loading && categories.length === 0 && (
        <p className="mt-8 text-sm text-genesis-muted">Загрузка каталога…</p>
      )}

      {categories.length === 0 && !loading && (
        <Card className="mt-8" padding="md">
          <p className="text-sm text-genesis-muted">
            Каталог временно недоступен.{" "}
            <ButtonLink href="/order" variant="primary" size="sm" className="inline-flex">
              Заказать landing →
            </ButtonLink>
          </p>
        </Card>
      )}

      {categories.map((cat) => (
        <section key={cat.id} className="mt-12 first:mt-0">
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
        <h2 className="text-xl font-bold">Куда развивается Genesis</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Цифровые отделы — vision, не готовый продукт в один клик.
        </p>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {(data?.business_units ?? []).map((u) => (
            <UnitCard key={u.id} unit={u} />
          ))}
        </div>
      </section>

      <Card className="mt-12 text-center" padding="md">
        <p className="text-sm text-genesis-muted">
          Много проектов в год?{" "}
          <ButtonLink href="/products" variant="ghost" size="sm" className="inline-flex text-indigo-300">
            Сравнить Genesis Studio →
          </ButtonLink>
        </p>
      </Card>
    </PublicPageShell>
  );
}
