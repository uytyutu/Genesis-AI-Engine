"use client";

import { GenesisConcierge } from "../components/GenesisConcierge";
import { GenesisChatErrorBoundary } from "../components/GenesisChatErrorBoundary";

export default function GenesisAIPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl px-4">
        <h1 className="mb-2 text-center text-2xl font-bold">Genesis CEO</h1>
        <p className="mb-6 text-center text-sm text-genesis-muted">
          Разговор с Genesis как с директором — отдельные чаты, общая долговременная память
        </p>
        <GenesisChatErrorBoundary>
          <GenesisConcierge scope="owner" />
        </GenesisChatErrorBoundary>
      </div>
    </main>
  );
}
