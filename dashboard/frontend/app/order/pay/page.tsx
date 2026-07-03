"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { formatEur } from "../../lib/formatEur";
import { formatApiDetail } from "../../lib/formatApiError";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function OrderPayContent() {
  const params = useSearchParams();
  const router = useRouter();
  const orderId = params.get("order_id") ?? "";
  const [status, setStatus] = useState<{
    business_name: string;
    package_name: string;
    price_eur: number;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!orderId) return;
    fetch(`${API}/api/sales/orders/${orderId}/status`)
      .then((r) => r.json())
      .then((body) => {
        if (body.business_name) setStatus(body);
      })
      .catch(() => setStatus(null));
  }, [orderId]);

  async function confirmSandboxPay() {
    if (!orderId) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/sales/orders/${orderId}/pay-sandbox`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(formatApiDetail(body.detail) || "Оплата не прошла");
        return;
      }
      router.push(`/order/status/${orderId}?paid=1`);
    } catch {
      setError("Сервер недоступен");
    } finally {
      setBusy(false);
    }
  }

  if (!orderId) {
    return (
      <main className="mx-auto max-w-lg py-12 text-center">
        <p className="text-genesis-muted">Заказ не найден</p>
        <Link href="/order" className="mt-4 inline-block text-genesis-accent hover:underline">
          ← Вернуться к заказу
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg py-10">
      <div className="rounded-3xl border border-genesis-accent/25 bg-genesis-panel p-8">
        <p className="genesis-label text-center">Оплата заказа</p>
        <h1 className="mt-2 text-center text-2xl font-bold">
          {status?.business_name ?? "Ваш заказ"}
        </h1>
        <p className="mt-2 text-center text-genesis-muted">
          {status?.package_name ?? "Лендинг"} ·{" "}
          {status ? formatEur(status.price_eur) : "…"}
        </p>
        <p className="mt-1 text-center text-xs text-genesis-muted">№ {orderId}</p>

        <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-xs text-amber-100/90">
          Тестовый режим оплаты (Sandbox). В продакшене здесь будет Stripe или другой
          провайдер. Деньги не списываются — только проверка процесса.
        </div>

        <button
          type="button"
          disabled={busy}
          onClick={confirmSandboxPay}
          className="mt-6 w-full rounded-xl bg-gradient-to-r from-emerald-500 to-genesis-accent py-3.5 text-sm font-semibold text-white disabled:opacity-50"
        >
          {busy ? "Обработка…" : "Подтвердить тестовую оплату"}
        </button>
        {error && <p className="mt-3 text-center text-xs text-rose-300">{error}</p>}

        <Link
          href={`/order/status/${orderId}`}
          className="mt-4 block text-center text-sm text-genesis-muted hover:text-genesis-text"
        >
          Отмена
        </Link>
      </div>
    </main>
  );
}

export default function OrderPayPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-lg py-12 text-center text-genesis-muted">
          Загрузка…
        </main>
      }
    >
      <OrderPayContent />
    </Suspense>
  );
}
