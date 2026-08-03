"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";

type ShopCard = {
  id: string;
  name: string;
  price: string;
  blurb: string;
  href: string;
  status: "live" | "soon";
};

const CARDS: ShopCard[] = [
  {
    id: "basic",
    name: "Landing Basic",
    price: "350 €",
    blurb: "Быстрый лендинг под нишу: ZIP, мобильный, путь к заявке.",
    href: "/order?market=DE&package=basic&form=1",
    status: "live",
  },
  {
    id: "business",
    name: "Landing Business",
    price: "650 €",
    blurb: "Больше секций и доверия — для локального бизнеса.",
    href: "/order?market=DE&package=business&form=1",
    status: "live",
  },
  {
    id: "premium",
    name: "Landing Premium",
    price: "1 200 €",
    blurb: "Индивидуальный акцент: визуал и структура под бренд.",
    href: "/order?market=DE&package=premium&form=1",
    status: "live",
  },
  {
    id: "bot",
    name: "Telegram + Website Chat",
    price: "от 499 €",
    blurb: "AI-сотрудник: сайт-чат и Telegram. WhatsApp — Coming Soon.",
    href: "/order/bot?package=bot_business",
    status: "live",
  },
  {
    id: "whatsapp",
    name: "WhatsApp",
    price: "—",
    blurb: "Business Cloud API через Meta OAuth — в разработке.",
    href: "/client/support",
    status: "soon",
  },
  {
    id: "instagram",
    name: "Instagram",
    price: "—",
    blurb: "Direct и бронирование — Coming Soon.",
    href: "/client/support",
    status: "soon",
  },
];

export default function ClientShopPage() {
  return (
    <ClientWorkspaceShell
      title="Магазин услуг"
      subtitle="Покупка только из кабинета — после профиля компании. Витрина остаётся рекламой."
    >
      <ul className="grid gap-3 sm:grid-cols-2">
        {CARDS.map((c) => (
          <li
            key={c.id}
            className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-lg font-semibold text-white">{c.name}</p>
              <span
                className={
                  c.status === "live"
                    ? "text-[10px] font-semibold uppercase tracking-wide text-emerald-300"
                    : "text-[10px] font-semibold uppercase tracking-wide text-amber-200/90"
                }
              >
                {c.status === "live" ? "Live" : "Soon"}
              </span>
            </div>
            <p className="mt-1 text-sm text-emerald-300/90">{c.price}</p>
            <p className="mt-2 flex-1 text-sm text-zinc-400">{c.blurb}</p>
            {c.status === "live" ? (
              <Link
                href={c.href}
                className="mt-4 inline-flex justify-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
              >
                Купить
              </Link>
            ) : (
              <span className="mt-4 inline-flex justify-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-500">
                Скоро
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-6 text-center text-sm text-zinc-500">
        <Link href="/client/onboarding" className="text-emerald-300 hover:underline">
          Сначала заполнить профиль компании →
        </Link>
      </p>
    </ClientWorkspaceShell>
  );
}
