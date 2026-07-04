"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import {
  fetchPricingDisplay,
  logPricingEvent,
  type PricingDisplay,
  type PricingTier,
} from "../lib/pricingApi";

function TierCard({ tier, page }: { tier: PricingTier; page: string }) {
  const isContact = tier.contact_only || tier.price_eur_month === null;
  const isWaitlist = !tier.available && !isContact;

  return (
    <div
      className={`relative flex flex-col rounded-2xl border p-6 ${
        tier.highlight
          ? "border-genesis-accent/30 bg-genesis-panel/50 opacity-90"
          : "border-genesis-border-subtle bg-genesis-panel/30"
      }`}
    >
      {isWaitlist && (
        <span className="absolute right-4 top-4 rounded-full border border-amber-500/30 bg-amber-950/40 px-2 py-0.5 text-[10px] uppercase tracking-wide text-amber-200">
          План
        </span>
      )}
      <p className="text-sm font-semibold text-genesis-muted">{tier.name}</p>
      <p className="mt-3 text-3xl font-bold tabular-nums text-genesis-text/90">
        {isWaitlist ? `~${tier.price_label}` : tier.price_label}
        {!isContact && (
          <span className="text-base font-normal text-genesis-muted">{tier.period}</span>
        )}
      </p>
      <p className="mt-2 text-xs text-genesis-muted">{tier.audience}</p>
      <ul className="mt-5 flex-1 space-y-2 text-sm text-genesis-muted">
        {tier.features.map((f) => (
          <li key={f} className="flex gap-2">
            <span className="text-genesis-muted">·</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <a
        href={tier.cta_href}
        onClick={() => logPricingEvent("cta_click", tier.id, page)}
        className={`mt-6 block rounded-xl py-3 text-center text-sm font-semibold ${
          isContact
            ? "bg-genesis-accent text-white"
            : "border border-genesis-border-subtle text-genesis-muted hover:border-genesis-accent/40 hover:text-white"
        }`}
      >
        {tier.cta}
      </a>
    </div>
  );
}

export default function PricingPage() {
  const [data, setData] = useState<PricingDisplay | null>(null);

  useEffect(() => {
    fetchPricingDisplay().then(setData);
    logPricingEvent("page_view", null, "pricing");
  }, []);

  const subs = data?.subscriptions ?? [];
  const platform = (data as PricingDisplay & { platform_status?: Record<string, string> })
    ?.platform_status;

  return (
    <PublicPageShell>

      <section className="rounded-2xl border border-amber-500/25 bg-gradient-to-br from-amber-950/25 to-genesis-panel p-6 text-center sm:p-10">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-300">
          🚧 {platform?.label ?? "Ранний доступ"}
        </p>
        <h1 className="mt-3 text-2xl font-bold sm:text-3xl">
          {platform?.headline ?? "Genesis Platform скоро откроется"}
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm text-genesis-muted">
          {platform?.body ??
            "Подписки откроются после публичного запуска. Ниже — ориентировочные планы, не активные тарифы."}
        </p>
        <a
          href={
            platform?.waitlist_href ??
            "mailto:hello@genesis-ai-engine.com?subject=Genesis%20Platform%20early%20access"
          }
          onClick={() => logPricingEvent("waitlist_cta", null, "pricing")}
          className="mt-6 inline-block rounded-xl bg-genesis-accent px-6 py-3 text-sm font-semibold text-white shadow-glow"
        >
          {platform?.waitlist_cta ?? "Стать одним из первых пользователей"}
        </a>
        <p className="mt-6 text-sm">
          <span className="text-genesis-muted">Нужен сайт уже сегодня? </span>
          <Link href="/order" className="font-medium text-emerald-400 hover:underline">
            Заказать landing →
          </Link>
        </p>
      </section>

      <section className="mt-12">
        <h2 className="text-center text-lg font-semibold text-genesis-muted">
          Планируемые тарифы (ориентир)
        </h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subs.map((tier) => (
            <TierCard key={tier.id} tier={tier} page="pricing" />
          ))}
        </div>
      </section>

      <p className="mt-10 text-center text-xs text-genesis-muted">
        {data?.disclaimer?.ru}
      </p>
    </PublicPageShell>
  );
}
