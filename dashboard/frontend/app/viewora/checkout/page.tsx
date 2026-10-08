"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchOrder, payDemo, paySandbox, setAccountId } from "../lib/api";

function CheckoutInner() {
  const params = useSearchParams();
  const router = useRouter();
  const orderId = params.get("order_id") || "";
  const mode = params.get("mode") || "demo";
  const [order, setOrder] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!orderId) return;
    fetchOrder(orderId)
      .then((r) => setOrder(r.order))
      .catch(() => setError("Заказ не найден"));
  }, [orderId]);

  async function pay() {
    if (!orderId) return;
    setBusy(true);
    setError("");
    try {
      const out =
        mode === "sandbox" ? await paySandbox(orderId) : await payDemo(orderId);
      if (out.account?.id) setAccountId(out.account.id);
      router.push(`/viewora/success?paid=1&order_id=${orderId}&mode=${out.payment_mode}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Payment failed");
    } finally {
      setBusy(false);
    }
  }

  if (!orderId) {
    return (
      <section className="viewora-section" style={{ borderTop: 0 }}>
        <h2>Checkout</h2>
        <p className="lead">Нет order_id. Выберите план на странице Pricing.</p>
        <Link href="/viewora/pricing" className="viewora-btn viewora-btn-primary">
          Pricing
        </Link>
      </section>
    );
  }

  return (
    <section className="viewora-section" style={{ borderTop: 0, maxWidth: 520 }}>
      <h2>Оплата Virtus Video AI</h2>
      <p className="lead">
        Professional AI Content Studio · безопасная оплата через Stripe (live) или Demo
        Bridge для проверки пути.
      </p>
      {order ? (
        <div className="viewora-price">
          <div className="viewora-muted">{String(order.label || "Virtus Video AI")}</div>
          <div className="amount">€{Number(order.amount_eur || 0)}</div>
          <div className="viewora-muted">
            {order.paid ? "Уже оплачено" : `Режим: ${mode}`}
          </div>
          {mode === "demo" ? (
            <div className="viewora-toast">
              Demo Payment Bridge · payment_mode=demo · не реальный доход
            </div>
          ) : null}
          {!order.paid ? (
            <button
              type="button"
              className="viewora-btn viewora-btn-primary"
              disabled={busy}
              onClick={pay}
            >
              {busy ? "…" : mode === "demo" ? "Оплатить (Demo)" : "Оплатить (Sandbox)"}
            </button>
          ) : (
            <Link href="/viewora/create" className="viewora-btn viewora-btn-primary">
              В Studio
            </Link>
          )}
        </div>
      ) : (
        <p className="viewora-muted">Загрузка заказа…</p>
      )}
      {error ? <div className="viewora-toast">{error}</div> : null}
      <p style={{ marginTop: "1.5rem" }}>
        <Link href="/viewora/legal/agb">AGB</Link> ·{" "}
        <Link href="/viewora/legal/datenschutz">Datenschutz</Link> ·{" "}
        <Link href="/viewora/legal/ki-hinweis">KI-Hinweis</Link>
      </p>
    </section>
  );
}

export default function VieworaCheckoutPage() {
  return (
    <Suspense fallback={<div className="viewora-panel">Checkout…</div>}>
      <CheckoutInner />
    </Suspense>
  );
}
