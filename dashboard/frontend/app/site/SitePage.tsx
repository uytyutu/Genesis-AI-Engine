"use client";

import { useEffect, useState } from "react";
import { formatEur } from "../lib/formatEur";
import { PublicPageShell } from "../components/PublicPageShell";
import { PublicPageHero } from "../components/PublicPageHero";
import { FaqList } from "../components/FaqList";
import { Badge, ButtonLink, Card } from "../components/ui";
import { Skeleton } from "../components/ui/Loader";

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

export function SitePage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/sales/packages`)
      .then((r) => r.json())
      .then((body) => setPackages(body.packages ?? []))
      .catch(() => setPackages([]))
      .finally(() => setLoading(false));
  }, []);

  const list = packages.length ? packages : FALLBACK_PACKAGES;
  const minPrice = Math.min(...list.map((p) => p.price_eur));

  return (
    <PublicPageShell>
      <PublicPageHero
        badge="Genesis Company"
        title={
          <>
            Современный сайт для вашего бизнеса —{" "}
            <span className="text-genesis-accent">под ключ</span>
          </>
        }
        description="Цена сразу на экране. Оплата онлайн. Прозрачный статус заказа. Без бесконечных созвонов и сюрпризов в счёте."
      >
        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
          <ButtonLink href="/order" variant="success" size="lg" className="w-full sm:w-auto">
            Заказать сайт — от {formatEur(minPrice)}
          </ButtonLink>
          <ButtonLink href="/services" variant="secondary" size="lg" className="w-full sm:w-auto">
            Смотреть услуги
          </ButtonLink>
        </div>
        <p className="mt-4 text-xs text-genesis-muted">
          Ответьте на 6 вопросов · увидите цену · оплатите · мы начнём работу
        </p>
      </PublicPageHero>

      <Card padding="lg" className="mt-8">
        <h2 className="text-xl font-bold">Кто мы и что делаем</h2>
        <p className="mt-3 text-sm leading-relaxed text-genesis-muted">
          Genesis — цифровая студия, которая создаёт одностраничные сайты (лендинги) для малого
          бизнеса: кафе, салоны, мастера, клиники, автосервисы, консультанты. Вы рассказываете о
          бизнесе — мы делаем сайт, который принимает заявки с телефона и компьютера.
        </p>
      </Card>

      <section className="mt-10" aria-labelledby="results-heading">
        <h2 id="results-heading" className="text-center text-xl font-bold">
          Что получает клиент
        </h2>
        <ul className="mt-6 grid gap-3 sm:grid-cols-2" role="list">
          {[
            "Современный дизайн под ваш бизнес",
            "Адаптация под мобильные — большинство клиентов с телефона",
            "Контакты, WhatsApp, форма заявки",
            "Базовое SEO — вас могут найти в Google",
            "Прозрачный статус заказа после оплаты",
            "Передача готового сайта для публикации",
          ].map((item) => (
            <li key={item}>
              <Card hover padding="sm" className="flex gap-3 text-sm">
                <span className="text-emerald-400" aria-hidden>
                  ✔
                </span>
                <span>{item}</span>
              </Card>
            </li>
          ))}
        </ul>
      </section>

      <Card padding="lg" className="mt-10">
        <h2 className="text-xl font-bold">Почему нам можно доверять</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {[
            { title: "Цена до заказа", text: "Вы видите пакет и стоимость до оплаты." },
            { title: "Процесс на виду", text: "Страница статуса после оплаты." },
            { title: "Сроки", text: "Ориентировочное время в заказе." },
          ].map((b) => (
            <Card key={b.title} hover={false} padding="sm" className="bg-genesis-bg/50">
              <p className="font-medium text-genesis-accent">{b.title}</p>
              <p className="mt-2 text-xs leading-relaxed text-genesis-muted">{b.text}</p>
            </Card>
          ))}
        </div>
      </Card>

      <section id="pricing" className="mt-12 scroll-mt-8" aria-labelledby="pricing-heading">
        <h2 id="pricing-heading" className="text-center text-xl font-bold">
          Сколько это стоит
        </h2>
        <p className="mt-2 text-center text-sm text-genesis-muted">
          Выберите пакет при заказе — цена не изменится после отправки формы
        </p>
        {loading ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48 w-full" />
            ))}
          </div>
        ) : (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {list.map((p, i) => (
              <Card key={p.id} glow={i === 1} padding="md" className={i === 1 ? "" : ""}>
                {i === 1 && (
                  <Badge variant="accent" className="mb-2">
                    Популярный
                  </Badge>
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
              </Card>
            ))}
          </div>
        )}
      </section>

      <Card padding="lg" className="mt-12">
        <h2 className="text-xl font-bold">Что будет после оплаты</h2>
        <ol className="mt-5 space-y-4">
          {[
            { n: "1", t: "Подтверждение", d: "Оплата получена, заказ принят." },
            { n: "2", t: "Производство", d: "Создаём сайт по вашим ответам." },
            { n: "3", t: "Статус", d: "Этапы и ориентировочный срок." },
            { n: "4", t: "Передача", d: "Готовый сайт и инструкция." },
          ].map((step) => (
            <li key={step.n} className="flex gap-4">
              <span
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-genesis-accent/20 text-sm font-bold text-genesis-accent"
                aria-hidden
              >
                {step.n}
              </span>
              <div>
                <p className="font-medium">{step.t}</p>
                <p className="text-sm text-genesis-muted">{step.d}</p>
              </div>
            </li>
          ))}
        </ol>
      </Card>

      <section className="mt-12" aria-labelledby="faq-heading">
        <h2 id="faq-heading" className="text-center text-xl font-bold">
          Частые вопросы
        </h2>
        <div className="mt-6">
          <FaqList items={FAQ} />
        </div>
      </section>

      <Card glow className="mt-14 border-emerald-500/30 bg-gradient-to-br from-emerald-950/30 to-genesis-panel text-center" padding="lg">
        <h2 className="text-2xl font-bold">Готовы начать?</h2>
        <p className="mt-3 text-genesis-muted">
          Заполните короткую форму — увидите цену и сможете оплатить онлайн
        </p>
        <ButtonLink href="/order" variant="success" size="lg" className="mt-6">
          Заказать сайт
        </ButtonLink>
      </Card>
    </PublicPageShell>
  );
}
