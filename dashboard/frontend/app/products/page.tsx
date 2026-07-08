"use client";

import { useEffect, useState } from "react";
import { PublicPageShell } from "../components/PublicPageShell";
import { Badge, ButtonLink, Card } from "../components/ui";
import {
  fetchPricingDisplay,
  formatComparisonCell,
  logPricingEvent,
  type PricingDisplay,
  type PricingTier,
} from "../lib/pricingApi";

function TierCard({ tier }: { tier: PricingTier }) {
  const isContact = tier.contact_only || tier.price_eur_month === null;
  const isWaitlist = !tier.available && !isContact;

  return (
    <Card glow={tier.highlight} padding="lg" className="relative flex flex-col">
      {isWaitlist && (
        <div className="absolute right-4 top-4">
          <Badge variant="warning">Скоро</Badge>
        </div>
      )}
      <p className="text-sm font-semibold text-genesis-muted">{tier.name}</p>
      <p className="mt-3 text-3xl font-bold tabular-nums">
        {tier.price_label}
        {!isContact && (
          <span className="text-base font-normal text-genesis-muted">{tier.period}</span>
        )}
      </p>
      {tier.tagline && <p className="mt-2 text-sm text-emerald-300/90">{tier.tagline}</p>}
      <p className="mt-1 text-xs text-genesis-muted">{tier.audience}</p>
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
        variant={tier.available ? "primary" : "secondary"}
        size="md"
        className="mt-6 w-full"
        onClick={() => logPricingEvent("cta_click", tier.id, "products")}
      >
        {tier.cta}
      </ButtonLink>
    </Card>
  );
}

export default function ProductsPage() {
  const [data, setData] = useState<PricingDisplay | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPricingDisplay().then((d) => {
      setData(d);
      setLoading(false);
    });
    logPricingEvent("page_view", null, "products");
  }, []);

  const caps = data?.capabilities;
  const svp = data?.service_vs_product;
  const anti = data?.anti_cannibalization;
  const comparison = data?.comparison;
  const subs = data?.subscriptions ?? [];
  const platform = data?.platform_status;

  return (
    <PublicPageShell>
      {loading && !caps && (
        <p className="text-sm text-genesis-muted">Загрузка каталога Studio…</p>
      )}
      {caps && (
        <section>
          <Badge variant="outline">Virtus Studio</Badge>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">{caps.headline}</h1>
          <p className="mt-4 max-w-2xl text-genesis-muted">{caps.subheadline}</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {caps.groups.map((g) => (
              <Card key={g.title} padding="md" className="border-indigo-500/15">
                <p className="font-semibold text-indigo-200">{g.title}</p>
                <ul className="mt-3 space-y-1.5 text-sm text-genesis-muted">
                  {g.items.map((item) => (
                    <li key={item}>· {item}</li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
          <p className="mt-6 text-sm text-genesis-muted">{caps.value_anchor}</p>
        </section>
      )}

      {svp && (
        <Card className="mt-12 border-emerald-500/20 bg-emerald-950/10" padding="lg">
          <h2 className="text-xl font-bold">{svp.headline}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-emerald-300">Разовая услуга</p>
              <p className="mt-2 text-sm text-genesis-muted">{svp.service_when}</p>
              <ButtonLink href={svp.cta_service.href} variant="secondary" size="sm" className="mt-3">
                {svp.cta_service.label} →
              </ButtonLink>
            </div>
            <div>
              <p className="text-sm font-medium text-indigo-300">Virtus Studio</p>
              <p className="mt-2 text-sm text-genesis-muted">{svp.product_when}</p>
              <ButtonLink href={svp.cta_product.href} variant="ghost" size="sm" className="mt-3">
                {svp.cta_product.label} ↓
              </ButtonLink>
            </div>
          </div>
        </Card>
      )}

      {anti && (
        <Card className="mt-8 border-amber-500/30 bg-amber-950/10" padding="lg">
          <h2 className="text-lg font-bold text-amber-100">{anti.headline}</h2>
          <p className="mt-3 text-sm text-genesis-muted">{anti.body}</p>
          <p className="mt-3 text-sm text-emerald-300/90">{anti.example_one_site}</p>
          <ButtonLink href="/services" variant="success" size="sm" className="mt-4">
            Заказать услугу под ключ →
          </ButtonLink>
        </Card>
      )}

      {comparison && (
        <section id="compare" className="mt-14 scroll-mt-8">
          <h2 className="text-xl font-bold">Сравнение возможностей</h2>
          <p className="mt-2 text-sm text-genesis-muted">
            Не «тарифы ради тарифов» — что вы получаете на каждом уровне.
          </p>
          <div className="mt-6 overflow-x-auto rounded-xl border border-genesis-border-subtle">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-genesis-border-subtle bg-genesis-elevated/50">
                  <th className="p-3 font-medium text-genesis-muted">Возможность</th>
                  {comparison.columns.map((col) => (
                    <th key={col.id} className="p-3 text-center font-semibold">
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparison.rows.map((row) => (
                  <tr key={row.feature} className="border-b border-white/5">
                    <td className="p-3 text-genesis-muted">{row.feature}</td>
                    {row.values.map((val, i) => (
                      <td key={i} className="p-3 text-center">
                        {formatComparisonCell(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="mt-14">
        <h2 className="text-lg font-semibold text-genesis-muted">Тарифы Studio</h2>
        {platform && (
          <Card className="mt-4 border-amber-500/25 bg-amber-950/15 text-center" padding="md">
            <Badge variant="warning">{platform.label}</Badge>
            <p className="mt-2 text-sm text-genesis-muted">{platform.body}</p>
          </Card>
        )}
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subs.map((tier) => (
            <TierCard key={tier.id} tier={tier} />
          ))}
        </div>
      </section>

      <p className="mt-10 text-center text-xs text-genesis-muted">{data?.disclaimer?.ru}</p>
    </PublicPageShell>
  );
}
