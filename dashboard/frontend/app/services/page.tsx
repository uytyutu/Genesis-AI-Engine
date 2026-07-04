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
  type PricingService,
} from "../lib/pricingApi";

function ServiceCard({ item }: { item: PricingService }) {
  const href = item.cta_href;
  const available = item.available;

  return (
    <Card
      glow={available}
      className={`relative flex flex-col ${
        available ? "border-emerald-500/35 bg-gradient-to-br from-emerald-950/20 to-genesis-panel" : ""
      }`}
      padding="lg"
    >
      <div className="absolute right-4 top-4">
        {available ? (
          <Badge variant="success">Доступно сейчас</Badge>
        ) : (
          <Badge variant="outline">По запросу</Badge>
        )}
      </div>
      <h3 className="pr-24 text-lg font-semibold">{item.name}</h3>
      <p className="mt-2 text-2xl font-bold text-genesis-accent">{item.price_label}</p>
      <p className="mt-3 flex-1 text-sm text-genesis-muted">{item.description}</p>
      {href.startsWith("mailto:") ? (
        <a
          href={href}
          onClick={() => logPricingEvent("service_cta", item.id, "services")}
          className={`mt-5 inline-flex items-center justify-center rounded-xl px-5 py-2.5 text-sm font-semibold transition-smooth ${
            available
              ? "bg-genesis-accent text-white shadow-glow hover:brightness-110"
              : "border border-genesis-border-subtle text-genesis-muted hover:text-white"
          }`}
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
      <p className="mt-4 text-xs text-genesis-muted">
        Направление развития Genesis — не готовый продукт сегодня.
      </p>
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

  useEffect(() => {
    fetchPricingDisplay().then(setData);
    logPricingEvent("page_view", null, "services");
  }, []);

  const services = data?.services ?? [];
  const availableNow = services.filter((s) => s.available);
  const onRequest = services.filter((s) => !s.available);

  return (
    <PublicPageShell>
      <PublicPageHero
        badge="Заказать сегодня"
        badgeVariant="success"
        title="Услуги Genesis"
        description="Решите задачу бизнеса — закажите сайт онлайн. Цена на экране, оплата через Stripe, статус заказа прозрачный."
      >
        <ButtonLink href="/order" variant="success" size="lg">
          Заказать сайт →
        </ButtonLink>
      </PublicPageHero>

      {availableNow.length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-emerald-300">Доступно сейчас</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {availableNow.map((s) => (
              <ServiceCard key={s.id} item={s} />
            ))}
          </div>
        </section>
      )}

      {onRequest.length > 0 && (
        <section className="mt-14">
          <h2 className="text-xl font-bold">Другие услуги — по запросу</h2>
          <p className="mt-2 text-sm text-genesis-muted">
            Обсудим scope и цену после Stripe Live и Gewerbe.
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {onRequest.map((s) => (
              <ServiceCard key={s.id} item={s} />
            ))}
          </div>
        </section>
      )}

      <section className="mt-16">
        <h2 className="text-xl font-bold">Куда развивается Genesis</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Цифровые отделы — vision, не то, что можно купить в один клик сегодня.
        </p>
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {(data?.business_units ?? []).map((u) => (
            <UnitCard key={u.id} unit={u} />
          ))}
        </div>
      </section>

      <p className="mt-10 text-center text-sm text-genesis-muted">
        Platform и подписки —{" "}
        <ButtonLink href="/pricing" variant="ghost" size="sm" className="inline-flex">
          ранний доступ
        </ButtonLink>
      </p>
    </PublicPageShell>
  );
}
