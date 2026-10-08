"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCatalog, startCheckout, type VieworaCatalog } from "../lib/api";

export default function VieworaPricingPage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<VieworaCatalog | null>(null);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCatalog()
      .then(setCatalog)
      .catch(() => setError("Каталог временно недоступен — обновите страницу."));
  }, []);

  async function buy(kind: "plan" | "credits", sku: string) {
    setBusy(sku);
    setError("");
    try {
      const out = await startCheckout({ kind, sku, email, prefer_demo: false });
      if (out.checkout_url.startsWith("http")) {
        window.location.href = out.checkout_url;
        return;
      }
      router.push(out.checkout_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="viewora-section" style={{ borderTop: 0, paddingTop: "1.5rem" }}>
      <h2>Простые цены. Реальная ценность.</h2>
      <p className="lead">
        FREE — 3 creations, чтобы почувствовать продукт. Дальше — подписка + credits
        (Short Video ≠ Podcast→20 по себестоимости). Оркестратор скрывает модели — вы видите
        «Создать».
      </p>

      <label className="viewora-label" htmlFor="vo-email">
        Email для чека (опционально)
      </label>
      <input
        id="vo-email"
        className="viewora-field"
        style={{ maxWidth: 360, marginBottom: "1.5rem", borderRadius: 999 }}
        type="email"
        placeholder="you@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      {error ? <div className="viewora-toast">{error}</div> : null}

      <div className="viewora-price-grid">
        {(catalog?.plans || []).map((plan) => (
          <article
            key={plan.id}
            className={`viewora-price${plan.popular ? " is-popular" : ""}`}
          >
            {plan.popular ? <span className="badge">POPULAR</span> : null}
            <div className="viewora-muted" style={{ fontWeight: 700 }}>
              {plan.name}
            </div>
            <div className="amount">
              {plan.monthly_eur === 0 ? "€0" : `€${plan.monthly_eur}`}
              {plan.monthly_eur > 0 ? (
                <span style={{ fontSize: "0.95rem", color: "var(--vo-muted)" }}>/mo</span>
              ) : null}
            </div>
            <div className="viewora-muted" style={{ fontSize: "0.85rem" }}>
              {plan.highlight}
            </div>
            <ul>
              {plan.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            {plan.id === "free" ? (
              <button
                type="button"
                className="viewora-btn viewora-btn-ghost"
                onClick={() => router.push("/viewora/create")}
              >
                Начать бесплатно
              </button>
            ) : (
              <button
                type="button"
                className="viewora-btn viewora-btn-primary"
                disabled={busy === plan.id}
                onClick={() => buy("plan", plan.id)}
              >
                {busy === plan.id ? "…" : "Выбрать"}
              </button>
            )}
          </article>
        ))}
      </div>

      <h2 style={{ marginTop: "3rem" }}>Credit Packs</h2>
      <p className="lead">Разные операции стоят разное — пакеты не сгорают.</p>
      <div className="viewora-price-grid">
        {(catalog?.credit_packs || []).map((pack) => (
          <article key={pack.id} className="viewora-price">
            <div className="amount">€{pack.eur}</div>
            <div className="viewora-muted">{pack.credits} credits</div>
            <button
              type="button"
              className="viewora-btn viewora-btn-gold"
              disabled={busy === pack.id}
              onClick={() => buy("credits", pack.id)}
            >
              {busy === pack.id ? "…" : "Купить"}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
