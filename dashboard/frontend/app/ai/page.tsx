"use client";

import { AssistantPanel } from "../components/AssistantPanel";

export default function GenesisAIPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg">
        <h1 className="mb-4 text-center text-2xl font-bold">Помощник Genesis</h1>
        <p className="mb-4 text-center text-sm text-genesis-muted">
          Ваш цифровой сотрудник — отвечает на основе данных компании
        </p>
        <p className="mb-6 text-center text-sm text-genesis-muted">
          Ваш помощник в цифровой компании — не ChatGPT, а знание вашей системы
        </p>
        <AssistantPanel embedded />
      </div>
    </main>
  );
}
