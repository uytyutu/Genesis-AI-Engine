import type { Metadata } from "next";
import Link from "next/link";
import { PublicPageShell } from "../components/PublicPageShell";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "FAQ",
  "Частые вопросы о заказе сайта через Genesis.",
  "/faq"
);

const FAQ = [
  {
    q: "Сколько ждать готовый сайт?",
    a: "От 48 часов для базового пакета после подтверждения оплаты. Точный срок виден на странице статуса заказа.",
  },
  {
    q: "Нужно ли что-то техническое от меня?",
    a: "Нет. Вы отвечаете на простые вопросы о бизнесе — мы делаем остальное.",
  },
  {
    q: "Как происходит оплата?",
    a: "После заказа вы видите цену и оплачиваете онлайн через защищённую платёжную систему Stripe.",
  },
  {
    q: "Могу ли я следить за прогрессом?",
    a: "Да. После оплаты вы получаете страницу статуса и письмо с ссылкой.",
  },
  {
    q: "Что если мне нужны правки?",
    a: "В пакеты Business и Premium входят раунды правок. Детали — при выборе пакета на странице заказа.",
  },
  {
    q: "Где правовая информация?",
    a: "Impressum, Datenschutz и AGB — в подвале сайта. Для вопросов — страница Kontakt.",
  },
];

export default function FaqPage() {
  return (
    <PublicPageShell>
      <main>
        <h1 className="text-center text-3xl font-bold">Частые вопросы</h1>
        <p className="mt-2 text-center text-genesis-muted">
          Ответы перед заказом сайта
        </p>
        <ul className="mt-10 space-y-3">
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
        <p className="mt-10 text-center">
          <Link
            href="/order"
            className="inline-block rounded-xl bg-genesis-accent px-8 py-3 text-sm font-semibold text-white shadow-glow"
          >
            Заказать сайт
          </Link>
        </p>
      </main>
    </PublicPageShell>
  );
}
