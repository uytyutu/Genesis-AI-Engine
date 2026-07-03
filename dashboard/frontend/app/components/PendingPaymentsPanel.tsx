"use client";

import { useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { useToast } from "./ToastProvider";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PendingPayment = {
  payment_id: string;
  amount_eur: number;
  label: string;
  provider: string;
  sender: string;
  received_at: string;
};

export function PendingPaymentsPanel({ payments }: { payments: PendingPayment[] }) {
  const { push } = useToast();
  const toastedRef = useRef<Set<string>>(new Set());

  const confirm = useCallback(
    async (payment: PendingPayment) => {
      const res = await fetch(
        `${API}/api/owner/finance/payments/${payment.payment_id}/confirm`,
        { method: "POST" },
      );
      if (!res.ok) return;
      push({
        title: `Платёж ${payment.amount_eur.toFixed(0)} € подтверждён`,
        tone: "success",
      });
      window.location.reload();
    },
    [push],
  );

  useEffect(() => {
    payments.forEach((p) => {
      if (toastedRef.current.has(p.payment_id)) return;
      toastedRef.current.add(p.payment_id);
      push({
        title: `Получен платёж: ${p.amount_eur.toFixed(0)} €`,
        body: `Отправитель: ${p.sender} · ${p.provider}`,
        tone: "payment",
        actionLabel: "Подтвердить",
        onAction: () => confirm(p),
      });
    });
  }, [payments, push, confirm]);

  if (payments.length === 0) return null;

  return (
    <section className="rounded-2xl border border-violet-500/30 bg-violet-950/20 p-5">
      <h2 className="text-sm font-semibold">💳 Требуется подтверждение оплаты</h2>
      <p className="mt-1 text-xs text-genesis-muted">
        Genesis не зачисляет средства автоматически — подтвердите каждый платёж.
      </p>
      <ul className="mt-4 space-y-3">
        {payments.map((p) => (
          <li
            key={p.payment_id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-genesis-border bg-genesis-panel/60 p-4"
          >
            <div>
              <p className="font-medium">Получен платёж: {p.amount_eur.toFixed(0)} €</p>
              <p className="text-xs text-genesis-muted">Отправитель: {p.sender}</p>
              <p className="text-xs text-genesis-muted">Способ оплаты: {p.provider}</p>
              <p className="text-xs text-genesis-muted">{p.label}</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => confirm(p)}
                className="rounded-lg bg-genesis-accent px-4 py-2 text-sm font-medium text-white"
              >
                Подтвердить
              </button>
              <Link
                href="/finance"
                className="rounded-lg border border-genesis-border px-4 py-2 text-sm"
              >
                Подробнее
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
