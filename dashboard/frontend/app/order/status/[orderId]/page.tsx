"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../../../components/PublicPageShell";
import { Button, ButtonLink, Loader } from "../../../components/ui";
import { formatLocalizedMoney } from "../../../lib/formatEur";
import { fetchPaymentReady, startOrderCheckout } from "../../../lib/orderCheckout";
import { publicApiBase } from "../../../lib/publicApiBase";
import { dateLocaleForUi } from "../../../lib/locale/dateLocale";
import { isUiLocale } from "../../../lib/locale/types";
import { useLocale } from "../../../context/LocaleContext";

const API = publicApiBase();

const PROVIDERS: { id: string; label: string }[] = [
  { id: "ionos", label: "IONOS" },
  { id: "hetzner", label: "Hetzner" },
  { id: "cloudflare_pages", label: "Cloudflare Pages" },
  { id: "vercel", label: "Vercel" },
  { id: "other", label: "Other" },
];

type TimelineStep = { id: string; label: string; done: boolean };

type AssistedGuide = {
  headline: string;
  trust: string[];
  never_stores: string[];
  variant_a: string;
  variant_b: string;
  providers: string[];
  hosting_provider: string | null;
};

type OrderStatus = {
  order_id: string;
  business_name: string;
  package_name: string;
  price_eur: number;
  price_label?: string | null;
  currency?: string | null;
  symbol?: string | null;
  market_code?: string | null;
  ui_lang?: string | null;
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
  download_ready?: boolean;
  download_url?: string | null;
  product_id?: string | null;
  review_eligible?: boolean;
  review_submitted?: boolean;
  review_url?: string | null;
  deployment_preference?: string;
  hosting_provider?: string | null;
  assisted_guide?: AssistedGuide | null;
};

function OrderStatusContent() {
  const { t, i18n } = useTranslation("site");
  const { applyUiLocale } = useLocale();
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
  const [deployBusy, setDeployBusy] = useState(false);
  const [deployError, setDeployError] = useState("");
  const [assistedOpen, setAssistedOpen] = useState(false);
  const [provider, setProvider] = useState("hetzner");

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
          try {
            const { logCommerceEvent } = await import("../../../lib/commerceFunnel");
            logCommerceEvent("checkout_paid", null, "order_status", {
              order_id: orderId,
            });
          } catch {
            /* analytics optional */
          }
        }
        const res = await fetch(`${API}/api/sales/orders/${orderId}/status`);
        if (res.ok) {
          const body = await res.json();
          if (!cancelled) {
            setData(body);
            if (body.hosting_provider) setProvider(body.hosting_provider);
            if (body.deployment_preference === "assisted") setAssistedOpen(true);
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    const tmr = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(tmr);
    };
  }, [orderId, justPaid]);

  useEffect(() => {
    const lang = data?.ui_lang;
    if (lang && isUiLocale(lang) && i18n.language !== lang) {
      applyUiLocale(lang);
    }
  }, [data?.ui_lang, applyUiLocale, i18n.language]);

  async function payNow() {
    setPayBusy(true);
    setPayError("");
    try {
      const url = await startOrderCheckout(orderId);
      window.location.href = url;
    } catch (e) {
      setPayError(e instanceof Error ? e.message : t("order.status.payFail"));
      setPayBusy(false);
    }
  }

  async function saveDeployment(preference: "zip_only" | "assisted", withProvider?: string) {
    setDeployBusy(true);
    setDeployError("");
    try {
      const body: { preference: string; hosting_provider?: string } = { preference };
      if (preference === "assisted" && withProvider) {
        body.hosting_provider = withProvider;
      }
      const res = await fetch(`${API}/api/sales/orders/${orderId}/deployment-preference`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || t("order.status.deployFail"));
      }
      const next = await res.json();
      setData(next);
      if (preference === "assisted") setAssistedOpen(true);
    } catch (e) {
      setDeployError(e instanceof Error ? e.message : t("order.status.deployFail"));
    } finally {
      setDeployBusy(false);
    }
  }

  async function copyReceipt() {
    if (!data?.client_receipt_text) return;
    const url = typeof window !== "undefined" ? window.location.href.split("?")[0] : "";
    const text = data.client_receipt_text.replace(
      `/order/status/${orderId}`,
      url || `/order/status/${orderId}`,
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
        <Loader label={t("order.status.loading")} />
      </PublicPageShell>
    );
  }

  if (!data) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-lg py-12 text-center">
          <p className="text-genesis-muted">{t("order.status.notFound")}</p>
          <Link href="/order" className="mt-4 inline-block text-genesis-accent hover:underline">
            {t("order.status.newOrder")}
          </Link>
        </main>
      </PublicPageShell>
    );
  }

  const showThankYou = justPaid || data.paid;
  const awaitingPayment = data.status === "awaiting_payment" && !data.paid;
  const dateLocale = dateLocaleForUi(i18n.language);
  const priceDisplay =
    (data.price_label && data.price_label.trim()) ||
    formatLocalizedMoney(data.price_eur, data.currency || "EUR");
  const pref = data.deployment_preference || "unset";
  const guide = data.assisted_guide;

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-lg py-6">
        <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/25 to-genesis-panel p-8 shadow-glow">
          {showThankYou && (
            <>
              <p className="text-center text-4xl">✓</p>
              <h1 className="mt-3 text-center text-2xl font-bold">{t("order.status.thanks")}</h1>
            </>
          )}
          {!showThankYou && (
            <p className="genesis-label text-center">{t("order.status.title")}</p>
          )}

          <p className="mt-4 text-center text-sm text-genesis-muted">
            {t("order.status.yourOrder")}{" "}
            <span className="font-mono text-genesis-text">№ {data.order_id}</span>
          </p>
          <p className="mt-1 text-center font-medium">{data.business_name}</p>
          <p className="text-center text-xs text-genesis-muted">
            {data.package_name} · {priceDisplay}
          </p>

          {awaitingPayment && paymentReady && (
            <div className="mt-6">
              <Button variant="success" size="lg" fullWidth loading={payBusy} onClick={payNow}>
                {payBusy
                  ? t("order.payBusy")
                  : t("order.payNow", { price: priceDisplay })}
              </Button>
              {payError && <p className="mt-2 text-center text-xs text-rose-300">{payError}</p>}
            </div>
          )}

          <div className="mt-6 rounded-2xl border border-genesis-border-subtle bg-genesis-bg/50 p-5">
            <p className="genesis-label">{t("order.status.status")}</p>
            <p className="mt-1 flex items-center justify-center gap-2 text-lg font-semibold text-emerald-300">
              {data.paid && <span>🟢</span>}
              {data.status_label}
            </p>

            {data.timeline.length > 0 && (
              <div className="mt-5">
                <p className="genesis-label">{t("order.status.progress")}</p>
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
                <p className="genesis-label">{t("order.status.next")}</p>
                <p className="mt-1 text-sm">{data.next_step}</p>
              </div>
            )}

            {(data.estimated_hours || data.estimated_delivery_at) && (
              <div className="mt-5">
                <p className="genesis-label">{t("order.status.eta")}</p>
                <p className="mt-1 text-sm font-medium">
                  {data.estimated_hours
                    ? t("order.status.etaHours", { hours: data.estimated_hours })
                    : data.estimated_delivery_at
                      ? new Date(data.estimated_delivery_at).toLocaleDateString(dateLocale)
                      : "—"}
                </p>
              </div>
            )}
          </div>

          {data.client_message && (
            <p className="mt-4 text-center text-sm text-genesis-muted">{data.client_message}</p>
          )}

          {data.paid && data.download_ready && (
            <>
              <a
                href={`${API}${data.download_url || `/api/sales/orders/${orderId}/download`}`}
                className="mt-5 flex w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:brightness-110"
              >
                {t("order.status.downloadZip")}
              </a>

              <div className="mt-5 rounded-2xl border border-sky-500/30 bg-sky-950/20 p-5">
                <p className="genesis-label">{t("order.status.deployTitle")}</p>

                {pref === "unset" && !assistedOpen && (
                  <div className="mt-3 grid gap-2">
                    <button
                      type="button"
                      disabled={deployBusy}
                      onClick={() => saveDeployment("zip_only")}
                      className="w-full rounded-xl border border-genesis-border-subtle bg-genesis-bg/60 px-4 py-3 text-sm font-semibold hover:bg-genesis-elevated disabled:opacity-50"
                    >
                      {t("order.status.deployZipOnly")}
                    </button>
                    <button
                      type="button"
                      disabled={deployBusy}
                      onClick={() => setAssistedOpen(true)}
                      className="w-full rounded-xl border border-sky-400/40 bg-sky-900/40 px-4 py-3 text-sm font-semibold text-sky-100 hover:bg-sky-900/60 disabled:opacity-50"
                    >
                      {t("order.status.deployAssisted")}
                    </button>
                  </div>
                )}

                {(assistedOpen || pref === "assisted") && pref !== "zip_only" && (
                  <div className="mt-3 space-y-3 text-sm">
                    <p className="font-medium text-sky-100">
                      {guide?.headline || t("order.status.deployAssisted")}
                    </p>
                    <label className="block">
                      <span className="text-xs text-genesis-muted">{t("order.status.deployProvider")}</span>
                      <select
                        className="mt-1 w-full rounded-lg border border-genesis-border-subtle bg-genesis-bg px-3 py-2"
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                      >
                        {PROVIDERS.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <Button
                      variant="success"
                      size="md"
                      fullWidth
                      loading={deployBusy}
                      onClick={() => saveDeployment("assisted", provider)}
                    >
                      {deployBusy ? t("order.status.deployBusy") : t("order.status.deployStart")}
                    </Button>

                    {guide && (
                      <>
                        <div>
                          <p className="genesis-label">{t("order.status.deployTrustTitle")}</p>
                          <ul className="mt-1 space-y-1 text-xs text-emerald-200/90">
                            {guide.trust.map((line) => (
                              <li key={line}>✔ {line}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="genesis-label">{t("order.status.deployNeverTitle")}</p>
                          <ul className="mt-1 space-y-1 text-xs text-rose-200/80">
                            {guide.never_stores.map((line) => (
                              <li key={line}>✗ {line}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-3">
                          <p className="text-xs font-semibold text-emerald-300">
                            {t("order.status.deployVariantA")}
                          </p>
                          <p className="mt-1 text-xs text-genesis-muted">{guide.variant_a}</p>
                          <p className="mt-3 text-xs font-semibold text-sky-300">
                            {t("order.status.deployVariantB")}
                          </p>
                          <p className="mt-1 text-xs text-genesis-muted">{guide.variant_b}</p>
                        </div>
                      </>
                    )}

                    {pref === "unset" && (
                      <button
                        type="button"
                        className="text-xs text-genesis-muted underline"
                        onClick={() => setAssistedOpen(false)}
                      >
                        ← {t("order.status.deployZipOnly")}
                      </button>
                    )}
                  </div>
                )}

                {pref === "zip_only" && (
                  <p className="mt-3 text-sm text-emerald-200/90">{t("order.status.deployZipChosen")}</p>
                )}
                {pref === "assisted" && (
                  <p className="mt-3 text-sm text-sky-100">{t("order.status.deployAssistedChosen")}</p>
                )}
                {deployError && <p className="mt-2 text-xs text-rose-300">{deployError}</p>}
              </div>
            </>
          )}

          {data.review_eligible && data.review_url && (
            <Link
              href={data.review_url}
              className="mt-3 flex w-full items-center justify-center rounded-xl border border-amber-400/40 bg-amber-950/30 px-4 py-3 text-sm font-semibold text-amber-100 hover:bg-amber-950/50"
            >
              ★ {t("order.status.leaveReview")}
            </Link>
          )}
          {data.review_submitted && (
            <p className="mt-3 text-center text-xs text-genesis-muted">
              {t("order.status.reviewSubmitted")}
            </p>
          )}

          {data.paid && data.client_receipt_text && (
            <button
              type="button"
              onClick={copyReceipt}
              className="mt-3 w-full rounded-xl border border-genesis-border-subtle py-2.5 text-xs text-genesis-muted hover:bg-genesis-elevated"
            >
              {copied ? t("order.status.copied") : t("order.status.copyReceipt")}
            </button>
          )}

          <p className="mt-4 text-center text-[10px] text-genesis-muted">{t("order.status.bookmark")}</p>

          <ButtonLink href="/order" variant="ghost" size="sm" className="mt-4">
            ← {t("order.status.newOrder")}
          </ButtonLink>
        </div>
      </main>
    </PublicPageShell>
  );
}

export default function OrderStatusPage() {
  const { t } = useTranslation("site");
  return (
    <Suspense
      fallback={
        <PublicPageShell>
          <main className="mx-auto max-w-lg py-12 text-center text-genesis-muted">
            {t("order.status.loading")}
          </main>
        </PublicPageShell>
      }
    >
      <OrderStatusContent />
    </Suspense>
  );
}
