"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../../components/PublicPageShell";
import { Button } from "../../components/ui";
import { formatEur } from "../../lib/formatEur";
import { fetchPaymentInfo, startOrderCheckout } from "../../lib/orderCheckout";
import { parseOrderPurchaseType } from "../../lib/orderTrustCard";
import { OrderTrustCard } from "../../components/OrderTrustCard";
import { OrderPayeeIdentity } from "../../components/OrderPayeeIdentity";
import { publicApiBase } from "../../lib/publicApiBase";
import { useLocale } from "../../context/LocaleContext";
import { isUiLocale } from "../../lib/locale/types";

const API = publicApiBase();

type PayStatus = {
  business_name: string;
  package_name: string;
  price_eur: number;
  paid: boolean;
  ui_lang?: string | null;
  price_label?: string | null;
};

function OrderPayContent() {
  const params = useSearchParams();
  const router = useRouter();
  const { t, i18n } = useTranslation("site");
  const { applyUiLocale } = useLocale();
  const orderId = params.get("order_id") ?? "";
  const [status, setStatus] = useState<PayStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [isSandbox, setIsSandbox] = useState(false);
  const [purchaseType, setPurchaseType] = useState<"one_time" | "subscription">("one_time");
  const [legalReady, setLegalReady] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setPurchaseType(parseOrderPurchaseType(new URLSearchParams(window.location.search).get("purchase_type")));
  }, []);

  useEffect(() => {
    if (!orderId) return;
    fetch(`${API}/api/sales/orders/${orderId}/status`)
      .then((r) => r.json())
      .then((body) => {
        if (body.business_name) {
          setStatus(body);
          if (body.paid) {
            router.replace(`/order/status/${orderId}`);
          }
        }
      })
      .catch(() => setStatus(null));
    fetchPaymentInfo().then((info) => setIsSandbox(info.sandbox));
    fetch(`${API}/api/public/legal/operator`)
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (body && typeof body.impressum_publishable === "boolean") {
          setLegalReady(body.impressum_publishable);
        }
      })
      .catch(() => setLegalReady(undefined));
  }, [orderId, router]);

  useEffect(() => {
    const lang = status?.ui_lang;
    if (!lang || !isUiLocale(lang)) return;
    if ((i18n.language || "").slice(0, 2) === lang.slice(0, 2)) return;
    applyUiLocale(lang);
  }, [status?.ui_lang, applyUiLocale, i18n.language]);

  async function pay() {
    if (!orderId) return;
    setBusy(true);
    setError("");
    try {
      if (isSandbox) {
        const res = await fetch(`${API}/api/sales/orders/${orderId}/pay-sandbox`, {
          method: "POST",
        });
        const body = await res.json();
        if (!res.ok) {
          setError(body.detail || t("pay.payFail"));
          return;
        }
        router.push(`/order/status/${orderId}?paid=1`);
        return;
      }
      const url = await startOrderCheckout(orderId);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof Error ? e.message : t("pay.serverDown"));
    } finally {
      setBusy(false);
    }
  }

  const priceText =
    status?.price_label || (status ? formatEur(status.price_eur) : "…");

  if (!orderId) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-lg py-12 text-center">
          <p className="text-genesis-muted">{t("pay.notFound")}</p>
          <Link href="/order" className="mt-4 inline-block text-genesis-accent hover:underline">
            {t("pay.backToOrder")}
          </Link>
        </main>
      </PublicPageShell>
    );
  }

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-lg py-6">
        <div className="rounded-3xl border border-genesis-accent/25 bg-genesis-panel p-8">
          <p className="genesis-label text-center">{t("pay.heading")}</p>
          <h1 className="mt-2 text-center text-2xl font-bold">
            {status?.business_name ?? t("pay.fallbackBusiness")}
          </h1>
          <p className="mt-2 text-center text-genesis-muted">
            {status?.package_name ?? t("pay.fallbackPackage")} · {priceText}
          </p>
          <p className="mt-1 text-center text-xs text-genesis-muted">№ {orderId}</p>

          {isSandbox && (
            <div className="mt-6 rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-xs text-amber-100/90">
              {t("pay.sandboxNote")}
            </div>
          )}

          <div className="mt-6 space-y-4">
            <OrderPayeeIdentity />
            <OrderTrustCard purchaseType={purchaseType} legalReady={legalReady} />
          </div>

          <Button
            variant="success"
            size="lg"
            fullWidth
            disabled={busy || !status}
            loading={busy}
            onClick={pay}
            className="mt-6"
          >
            {busy
              ? t("pay.processing")
              : status
                ? t("pay.payCta", { price: priceText })
                : t("pay.loading")}
          </Button>
          {error && <p className="mt-3 text-center text-xs text-rose-300">{error}</p>}

          <Link
            href={`/order/status/${orderId}`}
            className="mt-4 block text-center text-sm text-genesis-muted hover:text-genesis-text"
          >
            {t("pay.statusLink")}
          </Link>
        </div>
      </main>
    </PublicPageShell>
  );
}

export default function OrderPayPage() {
  return (
    <Suspense fallback={null}>
      <OrderPayContent />
    </Suspense>
  );
}
