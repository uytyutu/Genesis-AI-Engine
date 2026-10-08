"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function SuccessInner() {
  const params = useSearchParams();
  const mode = params.get("mode") || "stripe";
  const orderId = params.get("order_id") || "";

  return (
    <section className="Virtus Video AI-section" style={{ borderTop: 0 }}>
      <div className="Virtus Video AI-kicker">Payment confirmed</div>
      <h2>Добро пожаловать в Virtus Video AI</h2>
      <p className="lead">
        Подписка или credit pack активированы. Откройте Studio и создайте контент, который
        смотрят.
      </p>
      {mode === "demo" ? (
        <div className="Virtus Video AI-toast">
          Demo payment · payment_mode=demo · не учитывается как реальный доход
        </div>
      ) : null}
      {orderId ? (
        <p className="Virtus Video AI-muted" style={{ marginTop: "0.75rem" }}>
          Order: {orderId}
        </p>
      ) : null}
      <div className="Virtus Video AI-actions">
        <Link href="/Virtus Video AI/create" className="Virtus Video AI-btn Virtus Video AI-btn-primary">
          Open Studio
        </Link>
        <Link href="/Virtus Video AI" className="Virtus Video AI-btn Virtus Video AI-btn-ghost">
          Home
        </Link>
      </div>
    </section>
  );
}

export default function Virtus Video AISuccessPage() {
  return (
    <Suspense fallback={<div className="Virtus Video AI-panel">…</div>}>
      <SuccessInner />
    </Suspense>
  );
}
