"use client";

import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";

export default function GenesisAIPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl px-4">
        <h1 className="mb-2 text-center text-2xl font-bold">{ASSISTANT_NAME}</h1>
        <p className="mb-6 text-center text-sm text-genesis-muted">
          Разговор с {ASSISTANT_NAME} — {BRAND_NAME}. Отдельные чаты, общая долговременная память.
        </p>
        <GenesisChatErrorBoundary>
          <GenesisConcierge scope="owner" />
        </GenesisChatErrorBoundary>
      </div>
    </main>
  );
}
