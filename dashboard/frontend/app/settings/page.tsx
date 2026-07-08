"use client";

import Link from "next/link";

export default function SettingsPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-lg space-y-6">
        <h1 className="text-center text-2xl font-bold">Настройки</h1>
        <section className="rounded-xl border border-genesis-border bg-genesis-panel p-6 text-sm text-genesis-muted">
          <p>Имя владельца и параметры запуска настраиваются в приложении Virtus Core на рабочем столе.</p>
          <p className="mt-3">Версия платформы: 0.2</p>
        </section>
        <p className="text-center">
          <Link href="/" className="text-sm hover:text-white">
            ← На главную
          </Link>
        </p>
      </div>
    </main>
  );
}
