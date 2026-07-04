"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { PublicPageShell } from "../../../components/PublicPageShell";
import { formatEur } from "../../../lib/formatEur";
import { fetchPaymentReady, startOrderCheckout } from "../../../lib/orderCheckout";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type TimelineStep = { id: string; label: string; done: boolean };

type OrderStatus = {
  order_id: string;
  business_name: string;
  package_name: string;
  price_eur: number;
  status: string;
  status_label: string;
  current_step: string;
  next_step: string;
  timeline: TimelineStep[];
  estimated_delivery_at: string | null;
  estimated_hours: number | null;
  client_message: string;
  client_receipt_text: string;
  paid: boolean;
};

function OrderStatusContent() {
  const routeParams = useParams();
  const search = useSearchParams();
  const orderId = String(routeParams.orderId ?? "");
  const justPaid = search.get("paid") === "1";
  const [data, setData] = useState<OrderStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [payBusy, setPayBusy] = useState(false);
  const [payError, setPayError] = useState("");
  const [paymentReady, setPaymentReady] = useState(false);

  useEffect(() => {
    fetchPaymentReady().then(setPaymentReady);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        if (justPaid) {
          await fetch(`${API}/api/sales/orders/${orderId}/confirm-payment`, {
            method: "POST",
          });
        }
        const res = await fetch(`${API}/api/sales/orders/${orderId}/status`);
        if (res.ok) {
          const body = await res.json();
          if (!cancelled) setData(body);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    const t = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [orderId, justPaid]);

  async function payNow() {
    setPayBusy(true);
    setPayError("");
    try {
      const url = await startOrderCheckout(orderId);
      window.location.href = url;
    } catch (e) {
      setPayError(e instanceof Error ? e.message : "Не удалось начать оплату");
      setPayBusy(false);
    }
  }

  async function copyReceipt() {
    if (!data?.client_receipt_text) return;
    const url = typeof window !== "undefined" ? window.location.href.split("?")[0] : "";
    const text = data.client_receipt_text.replace(
      `/order/status/${orderId}`,
      url || `/order/status/${orderId}`
    );
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(false);
    }
  }

  if (loading) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-lg py-12 text-center text-sm text-genesis-muted">
          Загрузка статуса…
        </main>
      </PublicPageShell>
    );
  }

  if (!data) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-lg py-12 text-center">
          <p className="text-genesis-muted">Заказ не найден</p>
          <Link href="/order" className="mt-4 inline-block text-genesis-accent hover:underline">
            Заказать сайт
          </Link>
        </main>
      </PublicPageShell>
    );
  }

  const showThankYou = justPaid || data.paid;
  const awaitingPayment = data.status === "awaiting_payment" && !data.paid;

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-lg py-6">
        <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/25 to-genesis-panel p-8 shadow-glow">
          {showThankYou && (
            <>
              <p className="text-center text-4xl">✓</p>
              <h1 className="mt-3 text-center text-2xl font-bold">Спасибо!</h1>
            </>
          )}
          {!showThankYou && <p className="genesis-label text-center">Статус заказа</p>}

          <p className="mt-4 text-center text-sm text-genesis-muted">
            Ваш заказ <span className="font-mono text-genesis-text">№ {data.order_id}</span>
          </p>
          <p className="mt-1 text-center font-medium">{data.business_name}</p>
          <p className="text-center text-xs text-genesis-muted">
            {data.package_name} · {formatEur(data.price_eur)}
          </p>

          {awaitingPayment && paymentReady && (
            <div className="mt-6">
              <button
                type="button"
                disabled={payBusy}
                onClick={payNow}
                className="w-full rounded-xl bg-gradient-to-r from-emerald-500 to-genesis-accent py-3.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                {payBusy ? "Переход к оплате…" : `Оплатить ${formatEur(data.price_eur)}`}
              </button>
              {payError && <p className="mt-2 text-center text-xs text-rose-300">{payError}</p>}
            </div>
          )}

          <div className="mt-6 rounded-2xl border border-genesis-border-subtle bg-genesis-bg/50 p-5">
            <p className="genesis-label">Статус</p>
            <p className="mt-1 flex items-center justify-center gap-2 text-lg font-semibold text-emerald-300">
              {data.paid && <span>🟢</span>}
              {data.status_label}
            </p>

            {data.timeline.length > 0 && (
              <div className="mt-5">
                <p className="genesis-label">Прогресс</p>
                <ul className="mt-2 space-y-2 text-sm">
                  {data.timeline.map((step) => (
                    <li key={step.id} className="flex items-center gap-2">
                      <span className={step.done ? "text-emerald-400" : "text-genesis-muted"}>
                        {step.done ? "✔" : "○"}
                      </span>
                      <span className={step.done ? "text-genesis-text" : "text-genesis-muted"}>
                        {step.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data.next_step && (
              <div className="mt-5">
                <p className="genesis-label">Следующий этап</p>
                <p className="mt-1 text-sm">{data.next_step}</p>
              </div>
            )}

            {(data.estimated_hours || data.estimated_delivery_at) && (
              <div className="mt-5">
                <p className="genesis-label">Ориентировочное время</p>
                <p className="mt-1 text-sm font-medium">
                  {data.estimated_hours
                    ? `${data.estimated_hours} часов`
                    : data.estimated_delivery_at
                      ? new Date(data.estimated_delivery_at).toLocaleDateString("ru-RU")
                      : "—"}
                </p>
              </div>
            )}
          </div>

          {data.client_message && (
            <p className="mt-4 text-center text-sm text-genesis-muted">{data.client_message}</p>
          )}

          {data.paid && data.client_receipt_text && (
            <button
              type="button"
              onClick={copyReceipt}
              className="mt-5 w-full rounded-xl border border-genesis-border-subtle py-2.5 text-xs text-genesis-muted hover:bg-genesis-elevated"
            >
              {copied ? "Текст скопирован" : "Скопировать подтверждение"}
            </button>
          )}

          <p className="mt-4 text-center text-[10px] text-genesis-muted">
            Сохраните эту страницу — здесь всегда актуальный статус заказа.
          </p>

          <Link
            href="/order"
            className="mt-4 block text-center text-sm text-genesis-accent hover:underline"
          >
            ← Новый заказ
          </Link>
        </div>
      </main>
    </PublicPageShell>
  );
}

export default function OrderStatusPage() {
  return (
    <Suspense
      fallback={
        <PublicPageShell>
          <main className="mx-auto max-w-lg py-12 text-center text-genesis-muted">
            Загрузка…
          </main>
        </PublicPageShell>
      }
    >
      <OrderStatusContent />
    </Suspense>
  );
}
