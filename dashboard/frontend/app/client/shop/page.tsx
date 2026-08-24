"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { getClientToken } from "../../lib/clientAuth";
import { publicApiBase } from "../../lib/publicApiBase";
import { portalFetchAllow404 } from "../../lib/portalApi";
import {
  MARKETPLACE_LIVE,
  MARKETPLACE_SOON,
  marketplaceHref,
  resolveMarketplaceBadge,
  signalsFromOrdersAndProducts,
  type MarketplaceBadge,
  type MarketplaceServiceDef,
} from "../../lib/clientServiceMarketplace";

type OrderRow = {
  package_id?: string;
  product_kind?: string;
  status?: string;
  published_at?: string;
};

type ProductRow = {
  product_type?: string;
  product_id?: string;
};

function badgeLabel(b: MarketplaceBadge): string {
  if (b === "active") return "Aktiv";
  if (b === "activate") return "Nicht aktiviert";
  return "Coming Soon";
}

function badgeClass(b: MarketplaceBadge): string {
  if (b === "active")
    return "border-emerald-500/40 bg-emerald-950/40 text-emerald-200";
  if (b === "activate")
    return "border-sky-500/40 bg-sky-950/30 text-sky-100";
  return "border-white/10 bg-white/5 text-zinc-400";
}

function ctaLabel(badge: MarketplaceBadge, def: MarketplaceServiceDef): string {
  if (badge === "coming_soon") return "Coming Soon";
  if (badge === "active") return "Verwalten →";
  if (def.ctaKind === "order") return "Hinzufügen →";
  return "Hinzufügen →";
}

function ServiceRow({
  def,
  badge,
}: {
  def: MarketplaceServiceDef;
  badge: MarketplaceBadge;
}) {
  const href = marketplaceHref(def, badge);
  return (
    <li className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-lg font-semibold text-white">
            <span className="mr-2" aria-hidden>
              {def.icon}
            </span>
            {def.name}
          </p>
          {def.priceHint ? (
            <p className="mt-1 text-base font-semibold text-emerald-200/95">{def.priceHint}</p>
          ) : null}
        </div>
        <span
          className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badgeClass(badge)}`}
        >
          {badgeLabel(badge)}
        </span>
      </div>
      <p className="mt-2 text-sm text-genesis-muted">{def.blurb}</p>
      {(def.includes || []).length > 0 ? (
        <ul className="mt-3 space-y-1 text-sm text-zinc-300">
          {(def.includes || []).map((line) => (
            <li key={line} className="flex gap-2">
              <span className="text-emerald-400" aria-hidden>
                ✓
              </span>
              <span>{line}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="mt-4">
        {badge === "coming_soon" || !href ? (
          <span className="inline-flex min-h-[40px] items-center rounded-xl border border-white/10 px-4 text-sm text-zinc-500">
            Coming Soon
          </span>
        ) : (
          <Link
            href={href}
            className={
              badge === "active"
                ? "inline-flex min-h-[40px] items-center rounded-xl border border-emerald-400/40 px-4 text-sm font-semibold text-emerald-100 hover:bg-emerald-950/40"
                : "inline-flex min-h-[40px] items-center rounded-xl bg-emerald-500 px-4 text-sm font-semibold text-black hover:brightness-110"
            }
          >
            {ctaLabel(badge, def)}
          </Link>
        )}
      </div>
    </li>
  );
}

export default function ClientShopPage() {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [products, setProducts] = useState<ProductRow[]>([]);

  const load = useCallback(async () => {
    const token = getClientToken();
    const api = publicApiBase();
    if (token) {
      try {
        const res = await fetch(`${api}/api/client/orders`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (res.ok) {
          const body = await res.json();
          if (Array.isArray(body?.orders)) setOrders(body.orders);
        }
      } catch {
        /* ignore */
      }
    }
    try {
      const owned = await portalFetchAllow404<ProductRow[]>("/portal/my-products");
      if (Array.isArray(owned)) setProducts(owned);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const signals = useMemo(
    () => signalsFromOrdersAndProducts({ orders, products }),
    [orders, products],
  );

  const liveRows = useMemo(
    () =>
      MARKETPLACE_LIVE.map((def) => ({
        def,
        badge: resolveMarketplaceBadge(def, signals),
      })),
    [signals],
  );

  return (
    <ClientWorkspaceShell
      title="Service Marketplace"
      subtitle="Nur Module mit echtem Bestellweg — sonst Coming Soon, kein Fake-Aktivieren."
    >
      <p className="mb-6 max-w-2xl text-sm text-zinc-400">
        Aktiv → Verwalten. Nicht aktiviert → Hinzufügen (echte Bestellung). Coming Soon =
        Produkt noch nicht lieferbar.
      </p>

      <section className="mb-10">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-emerald-300/80">
          Verfügbare Services
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2">
          {liveRows.map(({ def, badge }) => (
            <ServiceRow key={def.id} def={def} badge={badge} />
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500">
          Coming Soon
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MARKETPLACE_SOON.map((def) => (
            <ServiceRow key={def.id} def={def} badge="coming_soon" />
          ))}
        </ul>
      </section>
    </ClientWorkspaceShell>
  );
}
