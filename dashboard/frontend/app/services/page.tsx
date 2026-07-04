"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
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
    <div
      className={`relative flex flex-col rounded-2xl border p-6 ${
        available
          ? "border-emerald-500/35 bg-gradient-to-br from-emerald-950/20 to-genesis-panel shadow-glow"
          : "border-genesis-border-subtle bg-genesis-panel/40"
      }`}
    >
      {available ? (
        <span className="absolute right-4 top-4 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
          Доступно сейчас
        </span>
      ) : (
        <span className="absolute right-4 top-4 rounded-full border border-genesis-border-subtle px-2 py-0.5 text-[10px] uppercase tracking-wide text-genesis-muted">
          По запросу
        </span>
      )}
      <h3 className="text-lg font-semibold pr-24">{item.name}</h3>
      <p className="mt-2 text-2xl font-bold text-genesis-accent">{item.price_label}</p>
      <p className="mt-3 flex-1 text-sm text-genesis-muted">{item.description}</p>
      {href.startsWith("mailto:") ? (
        <a
          href={href}
          onClick={() => logPricingEvent("service_cta", item.id, "services")}
          className={`mt-5 inline-block rounded-xl px-5 py-2.5 text-center text-sm font-semibold ${
            available
              ? "bg-genesis-accent text-white"
              : "border border-genesis-border-subtle"
          }`}
        >
          {item.cta}
        </a>
      ) : (
        <Link
          href={href}
          onClick={() => logPricingEvent("service_cta", item.id, "services")}
          className={`mt-5 inline-block rounded-xl px-5 py-2.5 text-center text-sm font-semibold ${
            available
              ? "bg-genesis-accent text-white"
              : "border border-genesis-border-subtle"
          }`}
        >
          {item.cta}
        </Link>
      )}
    </div>
  );
}

function UnitCard({ unit }: { unit: BusinessUnit }) {
  return (
    <div className="rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/20 to-genesis-panel/80 p-6">
      <span className="rounded-full border border-indigo-400/30 bg-indigo-950/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-200">
        Concept Preview
      </span>
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
      <a
        href={unit.cta_href}
        onClick={() => logPricingEvent("unit_cta", unit.id, "services")}
        className="mt-4 inline-block rounded-xl border border-indigo-400/30 px-4 py-2 text-sm text-indigo-200/90 hover:bg-indigo-950/40"
      >
        Узнать о планах
      </a>
    </div>
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

      <section className="py-10 text-center sm:py-14">
        <p className="genesis-label tracking-[0.2em] text-emerald-400">Заказать сегодня</p>
        <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Услуги Genesis</h1>
        <p className="mx-auto mt-4 max-w-2xl text-sm text-genesis-muted sm:text-base">
          Решите задачу бизнеса — закажите сайт онлайн. Цена на экране, оплата через Stripe,
          статус заказа прозрачный.
        </p>
        <Link
          href="/order"
          className="mt-8 inline-block rounded-2xl bg-gradient-to-r from-emerald-500 to-genesis-accent px-8 py-4 text-base font-semibold text-white shadow-glow"
        >
          Заказать сайт →
        </Link>
      </section>

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
        <Link href="/pricing" className="text-genesis-accent hover:underline">
          ранний доступ
        </Link>
      </p>
    </PublicPageShell>
  );
}
