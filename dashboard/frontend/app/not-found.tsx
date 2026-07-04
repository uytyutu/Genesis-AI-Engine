"use client";

import Link from "next/link";
import { PublicPageShell } from "./components/PublicPageShell";

export default function NotFound() {
  return (
    <PublicPageShell>
      <main className="py-16 text-center">
        <p className="text-6xl font-bold text-genesis-accent/80">404</p>
        <h1 className="mt-4 text-2xl font-bold">Страница не найдена</h1>
        <p className="mx-auto mt-3 max-w-md text-genesis-muted">
          Такой страницы нет. Вернитесь на главную или оформите заказ сайта.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href="/site"
            className="rounded-xl bg-genesis-accent px-6 py-3 text-sm font-semibold text-white"
          >
            На главную
          </Link>
          <Link
            href="/order"
            className="rounded-xl border border-genesis-border px-6 py-3 text-sm text-genesis-muted hover:text-white"
          >
            Заказать сайт
          </Link>
        </div>
      </main>
    </PublicPageShell>
  );
}
