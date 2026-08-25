"use client";

import { SalesOrdersPanel } from "../components/SalesOrdersPanel";

/** MC 2.0 — экран заказов владельца. */
export default function OrdersPage() {
  return (
    <main className="mx-auto max-w-4xl space-y-4 px-4 py-8 text-zinc-100">
      <header>
        <p className="text-[11px] uppercase tracking-wide text-zinc-500">
          Mission Control · Продажи
        </p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Заказы</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Кто купил · что · оплата · производство · Preview · ZIP · выдача.
          Только действия, которые реально вызывает API.
        </p>
      </header>
      <SalesOrdersPanel mode="desk" />
    </main>
  );
}
