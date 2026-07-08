"use client";

import { useEffect } from "react";
import { GenesisStatusPage } from "./components/GenesisStatusPage";
import { BRAND_NAME } from "./lib/publicBrand";
import { ButtonLink } from "./components/ui";

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
    <GenesisStatusPage
      code="500"
      title="Что-то пошло не так"
      description={`${BRAND_NAME} не смог загрузить эту страницу. Остановите и запустите приложение с рабочего стола — или нажмите «Повторить».`}
      onRetry={reset}
      actions={
        <>
          <button
            type="button"
            onClick={reset}
            className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow"
          >
            Повторить
          </button>
          <ButtonLink href="/" variant="secondary" size="md">
            На пульт
          </ButtonLink>
        </>
      }
    />
  );
}
