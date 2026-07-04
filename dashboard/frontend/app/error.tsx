"use client";

import { useEffect } from "react";
import Link from "next/link";
import { PublicPageShell } from "./components/PublicPageShell";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <PublicPageShell>
      <main className="py-16 text-center">
        <p className="text-6xl font-bold text-rose-400/80">500</p>
        <h1 className="mt-4 text-2xl font-bold">Что-то пошло не так</h1>
        <p className="mx-auto mt-3 max-w-md text-genesis-muted">
          Временная ошибка. Попробуйте обновить страницу или вернитесь позже.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-xl bg-genesis-accent px-6 py-3 text-sm font-semibold text-white"
          >
            Повторить
          </button>
          <Link
            href="/site"
            className="rounded-xl border border-genesis-border px-6 py-3 text-sm text-genesis-muted hover:text-white"
          >
            На главную
          </Link>
        </div>
      </main>
    </PublicPageShell>
  );
}
