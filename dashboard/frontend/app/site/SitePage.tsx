"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Package = {
  id: string;
  name: string;
  price_eur: number;
  deliverables: string[];
};

const FAQ = [
  {
    q: "Сколько ждать готовый сайт?",
    a: "От 48 часов для базового пакета после подтверждения оплаты. Точный срок виден в статусе заказа.",
  },
  {
    q: "Нужно ли что-то техническое от меня?",
    a: "Нет. Вы отвечаете на простые вопросы о бизнесе — мы делаем остальное.",
  },
  {
    q: "Как происходит оплата?",
    a: "После заказа вы видите цену и оплачиваете онлайн. Деньги поступают через защищённую платёжную систему.",
  },
  {
    q: "Могу ли я следить за прогрессом?",
    a: "Да. После оплаты вы получаете страницу статуса: что сделано, что происходит сейчас, ориентировочный срок.",
  },
  {
    q: "Что если мне нужны правки?",
    a: "В пакет Business и Premium входят раунды правок. Детали — в описании пакета при заказе.",
  },
];

export function SitePage() {
  const [packages, setPackages] = useState<Package[]>([]);

  useEffect(() => {
    fetch(`${API}/api/sales/packages`)
      .then((r) => r.json())
      .then((body) => setPackages(body.packages ?? []))
      .catch(() => setPackages([]));
  }, []);

  const minPrice = packages.length
    ? Math.min(...packages.map((p) => p.price_eur))
    : 350;

  return (
    <div className="mx-auto max-w-4xl px-4 pb-16 pt-6 sm:px-6">
      <header className="flex items-center justify-between gap-4 border-b border-white/5 pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-genesis-accent to-indigo-600 text-sm font-bold">
            G
          </div>
          <div>
            <p className="font-semibold tracking-tight">Genesis</p>
            <p className="text-[11px] text-genesis-muted">Сайты для бизнеса</p>
          </div>
        </div>
        <Link
          href="/order"
          className="hidden rounded-xl bg-genesis-accent px-4 py-2 text-sm font-semibold text-white shadow-glow sm:inline-block"
        >
          Заказать сайт
        </Link>
      </header>

      {/* Hero */}
      <section className="py-14 text-center sm:py-20">
        <p className="genesis-label tracking-[0.25em] text-genesis-accent">Genesis Company</p>
        <h1 className="mt-4 text-3xl font-bold leading-tight sm:text-5xl">
          Современный сайт для вашего бизнеса —{" "}
          <span className="text-genesis-accent">под ключ</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base text-genesis-muted sm:text-lg">
          Цена сразу на экране. Оплата онлайн. Прозрачный статус заказа. Без бесконечных
          созвонов и сюрпризов в счёте.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="/order"
            className="w-full rounded-2xl bg-gradient-to-r from-emerald-500 to-genesis-accent px-8 py-4 text-center text-base font-semibold text-white shadow-glow sm:w-auto"
          >
            Заказать сайт — от {formatEur(minPrice)}
          </Link>
          <a
            href="#pricing"
            className="w-full rounded-2xl border border-genesis-border-subtle px-8 py-4 text-center text-sm font-medium sm:w-auto"
          >
            Смотреть пакеты
          </a>
        </div>
        <p className="mt-4 text-xs text-genesis-muted">
          Ответьте на 6 вопросов · увидите цену · оплатите · мы начнём работу
        </p>
      </section>

      {/* Who / What */}
      <section className="genesis-card p-6 sm:p-8">
        <h2 className="text-xl font-bold">Кто мы и что делаем</h2>
        <p className="mt-3 text-sm leading-relaxed text-genesis-muted">
          Genesis — цифровая студия, которая создаёт одностраничные сайты (лендинги) для
          малого бизнеса: кафе, салоны, мастера, клиники, автосервисы, консультанты. Вы
          рассказываете о бизнесе — мы делаем сайт, который принимает заявки с телефона и
          компьютера.
        </p>
      </section>

      {/* Results */}
      <section className="mt-8">
        <h2 className="text-center text-xl font-bold">Что получает клиент</h2>
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {[
            "Современный дизайн под ваш бизнес",
            "Адаптация под мобильные — большинство клиентов с телефона",
            "Контакты, WhatsApp, форма заявки",
            "Базовое SEO — вас могут найти в Google",
            "Прозрачный статус заказа после оплаты",
            "Передача готового сайта для публикации",
          ].map((item) => (
            <li
              key={item}
              className="flex gap-3 rounded-xl border border-genesis-border-subtle bg-genesis-panel/40 px-4 py-3 text-sm"
            >
              <span className="text-emerald-400">✔</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Trust */}
      <section className="mt-10 genesis-card p-6 sm:p-8">
        <h2 className="text-xl font-bold">Почему нам можно доверять</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {[
            {
              title: "Цена до заказа",
              text: "Вы видите пакет и стоимость до оплаты. Без скрытых доплат.",
            },
            {
              title: "Процесс на виду",
              text: "После оплаты — страница статуса: что сделано и что происходит сейчас.",
            },
            {
              title: "Сроки",
              text: "Ориентировочное время выполнения фиксируется в заказе.",
            },
          ].map((b) => (
            <div key={b.title} className="rounded-xl bg-genesis-bg/50 p-4">
              <p className="font-medium text-genesis-accent">{b.title}</p>
              <p className="mt-2 text-xs leading-relaxed text-genesis-muted">{b.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="mt-12 scroll-mt-8">
        <h2 className="text-center text-xl font-bold">Сколько это стоит</h2>
        <p className="mt-2 text-center text-sm text-genesis-muted">
          Выберите пакет при заказе — цена не изменится после отправки формы
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {(packages.length ? packages : FALLBACK_PACKAGES).map((p, i) => (
            <div
              key={p.id}
              className={`rounded-2xl border p-5 ${
                i === 1
                  ? "border-genesis-accent/40 bg-genesis-accent/5 shadow-glow"
                  : "border-genesis-border-subtle bg-genesis-panel/50"
              }`}
            >
              {i === 1 && (
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-genesis-accent">
                  Популярный
                </p>
              )}
              <p className="font-semibold">{p.name}</p>
              <p className="mt-2 text-2xl font-bold tabular-nums">{formatEur(p.price_eur)}</p>
              <ul className="mt-4 space-y-1.5 text-xs text-genesis-muted">
                {p.deliverables.slice(0, 5).map((d) => (
                  <li key={d} className="flex gap-1.5">
                    <span className="text-emerald-400/80">✔</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* After payment */}
      <section className="mt-12 genesis-card p-6 sm:p-8">
        <h2 className="text-xl font-bold">Что будет после оплаты</h2>
        <ol className="mt-5 space-y-4">
          {[
            { n: "1", t: "Подтверждение", d: "Вы видите: оплата получена, заказ принят." },
            { n: "2", t: "Производство", d: "Мы создаём сайт по вашим ответам в форме." },
            { n: "3", t: "Статус", d: "На странице заказа — этапы и ориентировочный срок." },
            { n: "4", t: "Передача", d: "Готовый сайт и инструкция, как опубликовать." },
          ].map((step) => (
            <li key={step.n} className="flex gap-4">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-genesis-accent/20 text-sm font-bold text-genesis-accent">
                {step.n}
              </span>
              <div>
                <p className="font-medium">{step.t}</p>
                <p className="text-sm text-genesis-muted">{step.d}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* FAQ */}
      <section className="mt-12">
        <h2 className="text-center text-xl font-bold">Частые вопросы</h2>
        <ul className="mt-6 space-y-3">
          {FAQ.map((item) => (
            <li
              key={item.q}
              className="rounded-xl border border-genesis-border-subtle bg-genesis-panel/40 px-5 py-4"
            >
              <p className="font-medium">{item.q}</p>
              <p className="mt-2 text-sm text-genesis-muted">{item.a}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* CTA */}
      <section className="mt-14 rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/30 to-genesis-panel p-8 text-center">
        <h2 className="text-2xl font-bold">Готовы начать?</h2>
        <p className="mt-3 text-genesis-muted">
          Заполните короткую форму — увидите цену и сможете оплатить онлайн
        </p>
        <Link
          href="/order"
          className="mt-6 inline-block rounded-2xl bg-gradient-to-r from-emerald-500 to-genesis-accent px-10 py-4 text-base font-semibold text-white shadow-glow"
        >
          Заказать сайт
        </Link>
      </section>

      <footer className="mt-12 border-t border-white/5 pt-8 text-center text-xs text-genesis-muted">
        <p>Genesis Company · Лендинги для бизнеса</p>
        <p className="mt-2">
          <Link href="/order" className="text-genesis-accent hover:underline">
            Перейти к заказу
          </Link>
        </p>
      </footer>
    </div>
  );
}

const FALLBACK_PACKAGES: Package[] = [
  {
    id: "basic",
    name: "Landing Basic",
    price_eur: 350,
    deliverables: ["Современный сайт", "Мобильная версия", "SEO", "Контакты", "WhatsApp"],
  },
  {
    id: "business",
    name: "Landing Business",
    price_eur: 650,
    deliverables: ["Всё из Basic", "Карта", "Отзывы", "Логотип", "Правки"],
  },
  {
    id: "premium",
    name: "Landing Premium",
    price_eur: 1200,
    deliverables: ["Всё из Business", "Домен", "Премиум-дизайн", "Приоритет"],
  },
];
