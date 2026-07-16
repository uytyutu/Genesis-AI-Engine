"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

/**
 * CEO: Path A client surfaces. /site = offer page (no Vector chat). /order = checkout.
 */
export default function CeoSitePreviewPage() {
  const [origin, setOrigin] = useState("");

  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  const siteUrl = origin ? `${origin}/site` : "/site";
  const orderUrl = origin ? `${origin}/order` : "/order";

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-6 animate-fade-up px-4">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/40 to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">
            CEO · выход на рынок
          </p>
          <h1 className="mt-2 text-2xl font-semibold">Сайт для клиентов (Path A)</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Чат Vector с /site убран. Публичная витрина объясняет Neustart; заказ и оплата — на
            /order (CTA из писем Country Desk).
          </p>
        </header>

        <section className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5 space-y-3">
          <h2 className="text-lg font-semibold text-white">1. /site — витрина</h2>
          <p className="text-sm text-genesis-muted">
            Что продаём, пакеты, сроки. Без чата и без «сайт салона / кафе».
          </p>
          <a
            href={siteUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex rounded-lg border border-emerald-500/40 px-4 py-2 text-sm text-emerald-100 hover:bg-emerald-950/40"
          >
            Открыть /site →
          </a>
        </section>

        <section className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5 space-y-3">
          <h2 className="text-lg font-semibold text-white">2. /order — заказ и оплата</h2>
          <p className="text-sm text-genesis-muted">
            Анкета → подтверждение → Stripe (после Gewerbe). Сюда ведут sniper-письма.
          </p>
          <a
            href={orderUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:brightness-110"
          >
            Открыть /order →
          </a>
        </section>

        <div className="flex flex-wrap gap-2 text-sm">
          <Link
            href="/acquisition"
            className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-white/5"
          >
            Country Desk
          </Link>
          <Link
            href="/tiktok-horizon"
            className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-white/5"
          >
            TikTok Horizon (OFF)
          </Link>
        </div>
      </div>
    </main>
  );
}
