"use client";

import { useEffect } from "react";
import { PublicPageShell } from "./components/PublicPageShell";
import { Button, ButtonLink } from "./components/ui";

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
      <main className="py-16 text-center animate-fade-up">
        <p className="text-6xl font-bold text-rose-400/80">500</p>
        <h1 className="mt-4 text-2xl font-bold">Что-то пошло не так</h1>
        <p className="mx-auto mt-3 max-w-md text-genesis-muted">
          Временная ошибка. Попробуйте обновить страницу или вернитесь позже.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button variant="primary" size="md" onClick={reset}>
            Повторить
          </Button>
          <ButtonLink href="/site" variant="secondary" size="md">
            На главную
          </ButtonLink>
        </div>
      </main>
    </PublicPageShell>
  );
}
