"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../../../components/PublicPageShell";
import { Button, Loader } from "../../../components/ui";
import { publicApiBase } from "../../../lib/publicApiBase";

const API = publicApiBase();

function ReviewForm() {
  const { t } = useTranslation("site");
  const routeParams = useParams();
  const search = useSearchParams();
  const orderId = String(routeParams.orderId ?? "");
  const token = search.get("token") || "";

  const [stars, setStars] = useState(5);
  const [text, setText] = useState("");
  const [showCompany, setShowCompany] = useState(true);
  const [showLogo, setShowLogo] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = useMemo(
    () => Boolean(token) && text.trim().length >= 20 && text.trim().length <= 1000 && !busy,
    [token, text, busy],
  );

  async function submit() {
    if (!canSubmit) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/sales/orders/${orderId}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          stars,
          text: text.trim(),
          show_company_name: showCompany,
          show_logo: showLogo,
          company_display_name: companyName.trim() || null,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.detail || t("order.review.fail"));
      }
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("order.review.fail"));
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <main className="mx-auto max-w-lg py-12 text-center">
        <p className="text-genesis-muted">{t("order.review.missingToken")}</p>
        <Link href={`/order/status/${orderId}`} className="mt-4 inline-block text-emerald-300 hover:underline">
          {t("order.review.backStatus")}
        </Link>
      </main>
    );
  }

  if (done) {
    return (
      <main className="mx-auto max-w-lg py-12 text-center">
        <p className="text-lg font-semibold text-emerald-300">{t("order.review.success")}</p>
        <Link href={`/order/status/${orderId}`} className="mt-4 inline-block text-emerald-300 hover:underline">
          {t("order.review.backStatus")}
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg space-y-5 py-8">
      <header className="text-center">
        <h1 className="text-2xl font-bold text-white">{t("order.review.title")}</h1>
        <p className="mt-2 text-sm text-genesis-muted">{t("order.review.subtitle")}</p>
      </header>

      <div>
        <p className="text-xs uppercase tracking-wide text-white/50">{t("order.review.stars")}</p>
        <div className="mt-2 flex justify-center gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setStars(n)}
              className={`text-2xl ${n <= stars ? "text-amber-300" : "text-white/25"}`}
              aria-label={`${n}`}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      <label className="block text-sm">
        <span className="text-white/70">{t("order.review.text")}</span>
        <textarea
          className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 p-3 text-sm text-white"
          rows={5}
          maxLength={1000}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("order.review.textPh")}
        />
        <span className="mt-1 block text-right text-[10px] text-white/40">{text.trim().length}/1000</span>
      </label>

      <label className="flex items-center gap-2 text-sm text-white/80">
        <input type="checkbox" checked={showCompany} onChange={(e) => setShowCompany(e.target.checked)} />
        {t("order.review.showCompany")}
      </label>
      <label className="flex items-center gap-2 text-sm text-white/80">
        <input type="checkbox" checked={showLogo} onChange={(e) => setShowLogo(e.target.checked)} />
        {t("order.review.showLogo")}
      </label>

      {showCompany && (
        <label className="block text-sm">
          <span className="text-white/70">{t("order.review.companyName")}</span>
          <input
            className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 p-3 text-sm text-white"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            maxLength={200}
          />
        </label>
      )}

      {error && <p className="text-center text-xs text-rose-300">{error}</p>}

      <Button variant="success" size="lg" fullWidth disabled={!canSubmit} loading={busy} onClick={submit}>
        {busy ? t("order.review.busy") : t("order.review.submit")}
      </Button>

      <p className="text-center">
        <Link href={`/order/status/${orderId}`} className="text-xs text-genesis-muted hover:underline">
          {t("order.review.backStatus")}
        </Link>
      </p>
    </main>
  );
}

export default function OrderReviewPage() {
  const { t } = useTranslation("site");
  return (
    <PublicPageShell>
      <Suspense fallback={<Loader label={t("order.status.loading")} />}>
        <ReviewForm />
      </Suspense>
    </PublicPageShell>
  );
}
