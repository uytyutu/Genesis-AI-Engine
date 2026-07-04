"use client";

import { useEffect, useState } from "react";
import { PublicPageShell } from "../components/PublicPageShell";
import { Badge, ButtonLink, Card } from "../components/ui";
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
    <Card glow={tier.highlight} padding="lg" className="relative flex flex-col">
      {isWaitlist && (
        <div className="absolute right-4 top-4">
          <Badge variant="warning">План</Badge>
        </div>
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
            <span aria-hidden>·</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <ButtonLink
        href={tier.cta_href}
        variant={isContact ? "primary" : "secondary"}
        size="md"
        className="mt-6 w-full"
        onClick={() => logPricingEvent("cta_click", tier.id, page)}
      >
        {tier.cta}
      </ButtonLink>
    </Card>
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
      <Card
        className="border-amber-500/25 bg-gradient-to-br from-amber-950/25 to-genesis-panel text-center"
        padding="lg"
      >
        <Badge variant="warning">{platform?.label ?? "Ранний доступ"}</Badge>
        <h1 className="mt-3 text-2xl font-bold sm:text-3xl">
          {platform?.headline ?? "Genesis Platform скоро откроется"}
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm text-genesis-muted">
          {platform?.body ??
            "Подписки откроются после публичного запуска. Ниже — ориентировочные планы."}
        </p>
        <ButtonLink
          href={
            platform?.waitlist_href ??
            "mailto:hello@genesis-ai-engine.com?subject=Genesis%20Platform%20early%20access"
          }
          variant="primary"
          size="md"
          className="mt-6"
          onClick={() => logPricingEvent("waitlist_cta", null, "pricing")}
        >
          {platform?.waitlist_cta ?? "Стать одним из первых пользователей"}
        </ButtonLink>
        <p className="mt-6 text-sm">
          <span className="text-genesis-muted">Нужен сайт уже сегодня? </span>
          <ButtonLink href="/order" variant="ghost" size="sm" className="inline-flex text-emerald-400">
            Заказать landing →
          </ButtonLink>
        </p>
      </Card>

      <section className="mt-12" aria-labelledby="tiers-heading">
        <h2 id="tiers-heading" className="text-center text-lg font-semibold text-genesis-muted">
          Планируемые тарифы (ориентир)
        </h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subs.map((tier) => (
            <TierCard key={tier.id} tier={tier} page="pricing" />
          ))}
        </div>
      </section>

      <p className="mt-10 text-center text-xs text-genesis-muted">{data?.disclaimer?.ru}</p>
    </PublicPageShell>
  );
}
