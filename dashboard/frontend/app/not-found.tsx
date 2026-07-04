"use client";

import { PublicPageShell } from "./components/PublicPageShell";
import { ButtonLink } from "./components/ui";

export default function NotFound() {
  return (
    <PublicPageShell>
      <main className="py-16 text-center animate-fade-up">
        <p className="text-6xl font-bold text-genesis-accent/80">404</p>
        <h1 className="mt-4 text-2xl font-bold">Страница не найдена</h1>
        <p className="mx-auto mt-3 max-w-md text-genesis-muted">
          Такой страницы нет. Вернитесь на главную или оформите заказ сайта.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/site" variant="primary" size="md">
            На главную
          </ButtonLink>
          <ButtonLink href="/order" variant="secondary" size="md">
            Заказать сайт
          </ButtonLink>
        </div>
      </main>
    </PublicPageShell>
  );
}
