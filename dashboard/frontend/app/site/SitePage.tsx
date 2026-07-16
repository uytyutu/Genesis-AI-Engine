"use client";

import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { BRAND_NAME } from "../lib/publicBrand";

/**
 * Public Path A storefront — Landing Neustart.
 * Vector chat removed from /site (not the sniper/partner path). Buy flow = /order.
 */
export function SitePage() {
  return (
    <PublicPageShell>
      <div className="mx-auto max-w-3xl space-y-10 py-6 animate-fade-up">
        <header className="space-y-4 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/90">
            {BRAND_NAME}
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Landing Page · digitaler Neustart
          </h1>
          <p className="mx-auto max-w-2xl text-base text-genesis-muted sm:text-lg">
            Современная быстрая страница для вашего бизнеса: мобильная версия, понятный путь к
            записи или звонку. Не «починка» старого WordPress — новый чистый старт за 5–7 дней.
          </p>
        </header>

        <section className="grid gap-3 sm:grid-cols-3">
          {[
            { name: "Basic", price: "350 €", note: "Одна сильная страница" },
            { name: "Business", price: "650 €", note: "Основной пакет Mission 1" },
            { name: "Premium", price: "1 200 €", note: "Расширенный пакет" },
          ].map((p) => (
            <div
              key={p.name}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-center"
            >
              <p className="text-sm text-genesis-muted">{p.name}</p>
              <p className="mt-1 text-2xl font-semibold text-white">{p.price}</p>
              <p className="mt-1 text-xs text-white/60">{p.note}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/20 p-6">
          <h2 className="text-lg font-semibold text-white">Что вы получаете</h2>
          <ul className="mt-3 space-y-2 text-sm text-white/80">
            <li>• Готовая Landing Page (HTML), оптимизированная под телефон</li>
            <li>• Контакты, форма заявки, ясный призыв к действию</li>
            <li>• Базовое SEO и адаптация под экраны</li>
            <li>• Опционально: загрузка на ваш домен (Sorglos)</li>
          </ul>
          <p className="mt-4 text-sm text-genesis-muted">
            После оплаты производство запускается в Factory. Статус заказа — на странице оплаты.
          </p>
          <Link
            href="/order"
            className="mt-6 inline-flex rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:brightness-110"
          >
            Заказать Landing Page →
          </Link>
        </section>

        <p className="text-center text-xs text-genesis-muted">
          Virtus Core · Path A · не TikTok, не «починка CMS», не чат-конструктор.
        </p>
      </div>
    </PublicPageShell>
  );
}
