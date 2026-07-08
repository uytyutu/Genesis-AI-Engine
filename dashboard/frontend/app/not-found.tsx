"use client";

import { GenesisStatusPage } from "./components/GenesisStatusPage";
import { ButtonLink } from "./components/ui";

export default function NotFound() {
  return (
    <GenesisStatusPage
      code="404"
      title="Страница не найдена"
      description="Такой страницы нет в Virtus Core. Вернитесь на пульт или оформите заказ для клиента."
      actions={
        <>
          <ButtonLink href="/" variant="primary" size="md">
            На пульт
          </ButtonLink>
          <ButtonLink href="/order" variant="secondary" size="md">
            Заказать сайт
          </ButtonLink>
        </>
      }
    />
  );
}
