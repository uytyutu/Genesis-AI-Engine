import type { Metadata } from "next";
import { PublicPageShell } from "../components/PublicPageShell";
import { PublicPageHero } from "../components/PublicPageHero";
import { FaqList } from "../components/FaqList";
import { ButtonLink } from "../components/ui";
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
      <PublicPageHero
        title="Частые вопросы"
        description="Ответы перед заказом сайта"
      />
      <FaqList items={FAQ} />
      <p className="mt-10 text-center">
        <ButtonLink href="/order" variant="primary" size="lg">
          Заказать сайт
        </ButtonLink>
      </p>
    </PublicPageShell>
  );
}
