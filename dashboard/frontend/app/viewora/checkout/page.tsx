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
      router.push(`/Virtus Video AI/success?paid=1&order_id=${orderId}&mode=${out.payment_mode}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Payment failed");
    } finally {
      setBusy(false);
    }
  }

  if (!orderId) {
    return (
      <section className="Virtus Video AI-section" style={{ borderTop: 0 }}>
        <h2>Checkout</h2>
        <p className="lead">Нет order_id. Выберите план на странице Pricing.</p>
        <Link href="/Virtus Video AI/pricing" className="Virtus Video AI-btn Virtus Video AI-btn-primary">
          Pricing
        </Link>
      </section>
    );
  }

  return (
    <section className="Virtus Video AI-section" style={{ borderTop: 0, maxWidth: 520 }}>
      <h2>Оплата Virtus Video AI</h2>
      <p className="lead">
        Professional AI Content Studio · безопасная оплата через Stripe (live) или Demo
        Bridge для проверки пути.
      </p>
      {order ? (
        <div className="Virtus Video AI-price">
          <div className="Virtus Video AI-muted">{String(order.label || "Virtus Video AI")}</div>
          <div className="amount">€{Number(order.amount_eur || 0)}</div>
          <div className="Virtus Video AI-muted">
            {order.paid ? "Уже оплачено" : `Режим: ${mode}`}
          </div>
          {mode === "demo" ? (
            <div className="Virtus Video AI-toast">
              Demo Payment Bridge · payment_mode=demo · не реальный доход
            </div>
          ) : null}
          {!order.paid ? (
            <button
              type="button"
              className="Virtus Video AI-btn Virtus Video AI-btn-primary"
              disabled={busy}
              onClick={pay}
            >
              {busy ? "…" : mode === "demo" ? "Оплатить (Demo)" : "Оплатить (Sandbox)"}
            </button>
          ) : (
            <Link href="/Virtus Video AI/create" className="Virtus Video AI-btn Virtus Video AI-btn-primary">
              В Studio
            </Link>
          )}
        </div>
      ) : (
        <p className="Virtus Video AI-muted">Загрузка заказа…</p>
      )}
      {error ? <div className="Virtus Video AI-toast">{error}</div> : null}
      <p style={{ marginTop: "1.5rem" }}>
        <Link href="/Virtus Video AI/legal/agb">AGB</Link> ·{" "}
        <Link href="/Virtus Video AI/legal/datenschutz">Datenschutz</Link> ·{" "}
        <Link href="/Virtus Video AI/legal/ki-hinweis">KI-Hinweis</Link>
      </p>
    </section>
  );
}

export default function Virtus Video AICheckoutPage() {
  return (
    <Suspense fallback={<div className="Virtus Video AI-panel">Checkout…</div>}>
      <CheckoutInner />
    </Suspense>
  );
}
