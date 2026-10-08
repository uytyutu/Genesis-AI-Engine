"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function SuccessInner() {
  const params = useSearchParams();
  const mode = params.get("mode") || "stripe";
  const orderId = params.get("order_id") || "";

  return (
    <section className="viewora-section" style={{ borderTop: 0 }}>
      <div className="viewora-kicker">Payment confirmed</div>
      <h2>Добро пожаловать в Virtus Video AI</h2>
      <p className="lead">
        Подписка или credit pack активированы. Откройте Studio и создайте контент, который
        смотрят.
      </p>
      {mode === "demo" ? (
        <div className="viewora-toast">
          Demo payment · payment_mode=demo · не учитывается как реальный доход
        </div>
      ) : null}
      {orderId ? (
        <p className="viewora-muted" style={{ marginTop: "0.75rem" }}>
          Order: {orderId}
        </p>
      ) : null}
      <div className="viewora-actions">
        <Link href="/viewora/create" className="viewora-btn viewora-btn-primary">
          Open Studio
        </Link>
        <Link href="/viewora" className="viewora-btn viewora-btn-ghost">
          Home
        </Link>
      </div>
    </section>
  );
}

export default function VieworaSuccessPage() {
  return (
    <Suspense fallback={<div className="viewora-panel">…</div>}>
      <SuccessInner />
    </Suspense>
  );
}
