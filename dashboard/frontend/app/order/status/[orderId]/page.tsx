"use client";

import { Suspense, useEffect, useRef, useState } from "react";
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
import { rememberOrder } from "../../../lib/orderHistory";

const API = publicApiBase();

const PROVIDERS: { id: string; label: string; url?: string }[] = [
  { id: "ionos", label: "IONOS", url: "https://www.ionos.de/" },
  { id: "hetzner", label: "Hetzner", url: "https://www.hetzner.com/" },
  { id: "cloudflare_pages", label: "Cloudflare Pages", url: "https://pages.cloudflare.com/" },
  { id: "vercel", label: "Vercel", url: "https://vercel.com/" },
  { id: "other", label: "Other" },
];

type TimelineStep = { id: string; label: string; done: boolean; active?: boolean };

type AssistedGuide = {
  headline: string;
  trust: string[];
  never_stores: string[];
  variant_a: string;
  variant_b: string;
  providers: string[];
  hosting_provider: string | null;
};

type DeliveryItem = { id: string; label: string };
type PublishPayload = {
  state: string;
  label: string;
  published_url?: string | null;
  downloaded_at?: string | null;
  online_at?: string | null;
};
type NextOffer = {
  id: string;
  title: string;
  subtitle: string;
  bullets: string[];
  cta: string;
  interest_logged?: boolean;
};

type OrderStatus = {
  order_id: string;
  business_name: string;
  package_name: string;
  package_id?: string | null;
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
  estimated_minutes?: number | null;
  client_message: string;
  client_receipt_text: string;
  paid: boolean;
  paid_at?: string | null;
  download_ready?: boolean;
  download_url?: string | null;
  product_id?: string | null;
  review_eligible?: boolean;
  review_submitted?: boolean;
  review_url?: string | null;
  deployment_preference?: string;
  hosting_provider?: string | null;
  assisted_guide?: AssistedGuide | null;
  delivery_headline?: string | null;
  delivery_items?: DeliveryItem[];
  publish?: PublishPayload | null;
  next_offers?: NextOffer[];
};

function OrderStatusContent() {
  const { t, i18n } = useTranslation("site");
  const { applyUiLocale } = useLocale();
  const routeParams = useParams();
  const search = useSearchParams();
  const orderId = String(routeParams.orderId ?? "");
  const justPaid = search.get("paid") === "1";
  const justCanceled = search.get("canceled") === "1";
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
  const [goliveStep, setGoliveStep] = useState(1);
  const [publishUrl, setPublishUrl] = useState("");
  const [publishBusy, setPublishBusy] = useState(false);
  const [publishError, setPublishError] = useState("");
  const [interestBusy, setInterestBusy] = useState("");
  const downloadReadyRef = useRef(false);

  useEffect(() => {
    fetchPaymentReady().then(setPaymentReady);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let confirmed = false;
    let cancelLogged = false;
    async function load() {
      try {
        if (justPaid && !confirmed) {
          confirmed = true;
          await fetch(`${API}/api/sales/orders/${orderId}/confirm-payment`, {
            method: "POST",
          });
          try {
            const { logCommerceEvent } = await import("../../../lib/commerceFunnel");
            logCommerceEvent("checkout_paid", null, "order_status", {
              order_id: orderId,
            });
            logCommerceEvent("stripe_return_success", null, "order_status", {
              order_id: orderId,
              mode: "order_experience_v2",
            });
            logCommerceEvent("order_completed", null, "order_status", {
              order_id: orderId,
              mode: "order_experience_v2",
            });
          } catch {
            /* analytics optional */
          }
        } else if (justCanceled && !cancelLogged) {
          cancelLogged = true;
          try {
            const { logCommerceEvent } = await import("../../../lib/commerceFunnel");
            logCommerceEvent("stripe_return_cancel", null, "order_status", {
              order_id: orderId,
              mode: "order_experience_v2",
            });
          } catch {
            /* analytics optional */
          }
        }
        const res = await fetch(`${API}/api/sales/orders/${orderId}/status`);
        if (res.ok) {
          const body = (await res.json()) as OrderStatus;
          if (!cancelled) {
            setData(body);
            downloadReadyRef.current = Boolean(body.download_ready);
            if (body.hosting_provider) setProvider(body.hosting_provider);
            if (body.deployment_preference === "assisted") setAssistedOpen(true);
            if (body.publish?.published_url) setPublishUrl(body.publish.published_url);
            rememberOrder({
              order_id: body.order_id,
              business_name: body.business_name,
              package_name: body.package_name,
              price_label: body.price_label || undefined,
              market_code: body.market_code || undefined,
              status: body.status,
            });
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    const tmr = setInterval(() => {
      void load();
    }, 2500);
    return () => {
      cancelled = true;
      clearInterval(tmr);
    };
  }, [orderId, justPaid, justCanceled]);

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

  async function savePublish(state: "downloaded" | "online") {
    setPublishBusy(true);
    setPublishError("");
    try {
      const res = await fetch(`${API}/api/sales/orders/${orderId}/publish-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state,
          published_url: state === "online" ? publishUrl.trim() : undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || t("order.status.deployFail"));
      }
      setData(await res.json());
    } catch (e) {
      setPublishError(e instanceof Error ? e.message : t("order.status.deployFail"));
    } finally {
      setPublishBusy(false);
    }
  }

  async function saveInterest(offerId: string) {
    setInterestBusy(offerId);
    try {
      const res = await fetch(`${API}/api/sales/orders/${orderId}/next-offer-interest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ offer_id: offerId }),
      });
      if (res.ok) setData(await res.json());
    } finally {
      setInterestBusy("");
    }
  }

  async function onDownloadClick() {
    if (data?.publish?.state === "not_downloaded") {
      void savePublish("downloaded");
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
  const building = data.paid && !data.download_ready;
  const etaMinutes = data.estimated_minutes ?? 15;

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-lg py-6">
        <div className="rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/25 to-genesis-panel p-8 shadow-glow">
          {showThankYou && (
            <>
              <p className="text-center text-4xl">✓</p>
              <h1 className="mt-3 text-center text-2xl font-bold">{t("order.status.thanks")}</h1>
              {data.paid && (
                <p className="mt-2 text-center text-sm text-emerald-300">
                  {t("order.status.paymentReceived")} · {t("order.status.orderAccepted")}
                </p>
              )}
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
              {data.download_ready ? "🟢" : data.paid ? "🟡" : "○"}
              {data.status_label}
            </p>

            {data.timeline.length > 0 && (
              <div className="mt-5">
                <p className="genesis-label">{t("order.status.progress")}</p>
                <ul className="mt-2 space-y-2 text-sm">
                  {data.timeline.map((step) => (
                    <li key={step.id} className="flex items-center gap-2">
                      <span
                        className={
                          step.done
                            ? "text-emerald-400"
                            : step.active
                              ? "text-amber-300"
                              : "text-genesis-muted"
                        }
                      >
                        {step.done ? "✔" : step.active ? "🟡" : "⬜"}
                      </span>
                      <span
                        className={
                          step.done || step.active ? "text-genesis-text" : "text-genesis-muted"
                        }
                      >
                        {step.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {building && (
              <p className="mt-4 text-center text-sm text-amber-200/90">
                {t("order.status.building")}
              </p>
            )}

            {data.next_step && (
              <div className="mt-5">
                <p className="genesis-label">{t("order.status.next")}</p>
                <p className="mt-1 text-sm">{data.next_step}</p>
              </div>
            )}

            {data.paid && !data.download_ready && (
              <div className="mt-5">
                <p className="genesis-label">{t("order.status.eta")}</p>
                <p className="mt-1 text-sm font-medium">
                  {t("order.status.etaMinutes", { minutes: etaMinutes })}
                </p>
              </div>
            )}
          </div>

          {data.client_message && (
            <p className="mt-4 text-center text-sm text-genesis-muted">{data.client_message}</p>
          )}

          {/* Download — active only when ZIP ready */}
          {data.paid && (
            <div className="mt-5">
              {data.download_ready ? (
                <a
                  href={`${API}${data.download_url || `/api/sales/orders/${orderId}/download`}`}
                  onClick={onDownloadClick}
                  className="flex w-full items-center justify-center rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:brightness-110"
                >
                  {t("order.status.downloadZip")}
                </a>
              ) : (
                <button
                  type="button"
                  disabled
                  className="flex w-full cursor-not-allowed items-center justify-center rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 px-4 py-3 text-sm font-semibold text-genesis-muted opacity-70"
                >
                  {t("order.status.downloadZip")}
                </button>
              )}
              {!data.download_ready && (
                <p className="mt-2 text-center text-[11px] text-genesis-muted">
                  {t("order.status.downloadSoon")}
                </p>
              )}
            </div>
          )}

          {/* Value reveal — what was created */}
          {data.paid && data.download_ready && (data.delivery_items?.length ?? 0) > 0 && (
            <div className="mt-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5">
              <p className="text-center text-lg font-semibold text-emerald-200">
                {data.delivery_headline || t("order.status.siteReadyTitle")}
              </p>
              <p className="mt-3 genesis-label text-center">{t("order.status.createdLabel")}</p>
              <ul className="mt-2 grid gap-1.5 text-sm sm:grid-cols-2">
                {data.delivery_items!.map((item) => (
                  <li key={item.id} className="flex items-center gap-2 text-genesis-text">
                    <span className="text-emerald-400">✔</span>
                    {item.label}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Publish status: downloaded vs online */}
          {data.paid && data.download_ready && data.publish && (
            <div className="mt-5 rounded-2xl border border-genesis-border-subtle bg-genesis-bg/40 p-5">
              <p className="genesis-label">{t("order.status.publishTitle")}</p>
              <p className="mt-2 flex items-center gap-2 text-sm font-medium">
                {data.publish.state === "online" ? "🟢" : data.publish.state === "downloaded" ? "🟡" : "⬜"}
                {data.publish.label}
              </p>
              {data.publish.state === "online" && data.publish.published_url && (
                <a
                  href={data.publish.published_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 block break-all text-sm text-sky-300 underline"
                >
                  {data.publish.published_url}
                </a>
              )}
              {data.publish.state !== "online" && (
                <div className="mt-3 space-y-2">
                  {data.publish.state === "not_downloaded" && (
                    <button
                      type="button"
                      disabled={publishBusy}
                      onClick={() => savePublish("downloaded")}
                      className="w-full rounded-xl border border-genesis-border-subtle px-3 py-2 text-xs font-semibold hover:bg-genesis-elevated disabled:opacity-50"
                    >
                      {t("order.status.markDownloaded")}
                    </button>
                  )}
                  <label className="block text-xs text-genesis-muted">
                    {t("order.status.markOnline")}
                    <input
                      className="mt-1 w-full rounded-lg border border-genesis-border-subtle bg-genesis-bg px-3 py-2 text-sm text-genesis-text"
                      placeholder={t("order.status.onlineUrlPh")}
                      value={publishUrl}
                      onChange={(e) => setPublishUrl(e.target.value)}
                    />
                  </label>
                  <button
                    type="button"
                    disabled={publishBusy || !publishUrl.trim()}
                    onClick={() => savePublish("online")}
                    className="w-full rounded-xl bg-sky-700 px-3 py-2 text-xs font-semibold text-white hover:brightness-110 disabled:opacity-50"
                  >
                    {publishBusy ? t("order.status.onlineBusy") : t("order.status.onlineSave")}
                  </button>
                </div>
              )}
              {publishError && <p className="mt-2 text-xs text-rose-300">{publishError}</p>}
            </div>
          )}

          {/* LTV next offers — AI Business Assistant first */}
          {data.paid && data.download_ready && (data.next_offers?.length ?? 0) > 0 && (
            <div className="mt-5 space-y-3">
              <p className="genesis-label">{t("order.status.nextProductsTitle")}</p>
              {data.next_offers!.map((offer) => (
                <div
                  key={offer.id}
                  className="rounded-2xl border border-violet-500/25 bg-violet-950/15 p-4"
                >
                  <p className="font-semibold text-violet-100">{offer.title}</p>
                  <p className="mt-1 text-xs text-genesis-muted">{offer.subtitle}</p>
                  <ul className="mt-2 space-y-1 text-xs text-genesis-text">
                    {offer.bullets.map((b) => (
                      <li key={b}>· {b}</li>
                    ))}
                  </ul>
                  {offer.interest_logged ? (
                    <p className="mt-3 text-xs text-emerald-300">{t("order.status.interestSaved")}</p>
                  ) : (
                    <button
                      type="button"
                      disabled={interestBusy === offer.id}
                      onClick={() => saveInterest(offer.id)}
                      className="mt-3 rounded-lg border border-violet-400/40 bg-violet-900/40 px-3 py-2 text-xs font-semibold text-violet-100 hover:bg-violet-900/60 disabled:opacity-50"
                    >
                      {interestBusy === offer.id
                        ? t("order.status.interestBusy")
                        : offer.cta}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Beginner go-live wizard after ZIP ready */}
          {data.paid && data.download_ready && (
            <div className="mt-5 rounded-2xl border border-sky-500/30 bg-sky-950/20 p-5">
              <p className="genesis-label">{t("order.status.goliveTitle")}</p>

              <div className="mt-3 flex gap-2 text-[10px] font-semibold uppercase tracking-wide text-genesis-muted">
                {[1, 2, 3].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setGoliveStep(n)}
                    className={`rounded-full px-2.5 py-1 ${
                      goliveStep === n
                        ? "bg-sky-500/30 text-sky-100"
                        : "bg-genesis-bg/40 hover:bg-genesis-elevated"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>

              {goliveStep === 1 && (
                <div className="mt-3 space-y-2 text-sm">
                  <p className="font-medium text-sky-100">{t("order.status.goliveStep1")}</p>
                  <p className="text-xs text-genesis-muted">{t("order.status.goliveStep1Hint")}</p>
                  <div className="flex flex-wrap gap-2">
                    <a
                      href="https://www.ionos.de/"
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg border border-genesis-border-subtle px-3 py-2 text-xs hover:bg-genesis-elevated"
                    >
                      {t("order.status.openIonos")}
                    </a>
                    <a
                      href="https://www.hetzner.com/"
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg border border-genesis-border-subtle px-3 py-2 text-xs hover:bg-genesis-elevated"
                    >
                      {t("order.status.openHetzner")}
                    </a>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => setGoliveStep(2)}>
                    → {t("order.status.goliveStep2")}
                  </Button>
                </div>
              )}

              {goliveStep === 2 && (
                <div className="mt-3 space-y-2 text-sm">
                  <p className="font-medium text-sky-100">{t("order.status.goliveStep2")}</p>
                  <p className="text-xs text-genesis-muted">{t("order.status.goliveStep2Hint")}</p>
                  <ul className="space-y-1 text-xs text-genesis-muted">
                    {PROVIDERS.filter((p) => p.url).map((p) => (
                      <li key={p.id}>
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-200 underline hover:text-sky-100"
                        >
                          {p.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                  <Button size="sm" variant="ghost" onClick={() => setGoliveStep(3)}>
                    → {t("order.status.goliveStep3")}
                  </Button>
                </div>
              )}

              {goliveStep === 3 && (
                <div className="mt-3 space-y-2 text-sm">
                  <p className="font-medium text-sky-100">{t("order.status.goliveStep3")}</p>
                  <p className="text-xs text-genesis-muted">{t("order.status.goliveStep3Hint")}</p>
                  <p className="text-xs font-medium text-amber-100/90">
                    {t("order.status.goliveNeedHelp")}
                  </p>
                </div>
              )}

              <div className="mt-4 border-t border-sky-500/20 pt-4">
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
                      <span className="text-xs text-genesis-muted">
                        {t("order.status.deployProvider")}
                      </span>
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
                  <p className="mt-3 text-sm text-emerald-200/90">
                    {t("order.status.deployZipChosen")}
                  </p>
                )}
                {pref === "assisted" && (
                  <p className="mt-3 text-sm text-sky-100">
                    {t("order.status.deployAssistedChosen")}
                  </p>
                )}
                {deployError && <p className="mt-2 text-xs text-rose-300">{deployError}</p>}
              </div>
            </div>
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

          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {data.paid && (
              <Link
                href={`/order/receipt/${orderId}`}
                className="rounded-xl border border-genesis-border-subtle py-2.5 text-center text-xs text-genesis-muted hover:bg-genesis-elevated"
              >
                {t("order.status.viewReceipt")}
              </Link>
            )}
            {data.paid && data.client_receipt_text && (
              <button
                type="button"
                onClick={copyReceipt}
                className="rounded-xl border border-genesis-border-subtle py-2.5 text-xs text-genesis-muted hover:bg-genesis-elevated"
              >
                {copied ? t("order.status.copied") : t("order.status.copyReceipt")}
              </button>
            )}
          </div>

          <p className="mt-4 text-center text-[10px] text-genesis-muted">
            {t("order.status.bookmark")}
          </p>

          <div className="mt-4 flex flex-wrap justify-center gap-3 text-sm">
            <Link href="/order/history" className="text-genesis-accent hover:underline">
              {t("order.status.orderHistory")}
            </Link>
            <ButtonLink href="/order" variant="ghost" size="sm">
              ← {t("order.status.newOrder")}
            </ButtonLink>
          </div>

          {data.paid_at && (
            <p className="mt-3 text-center text-[10px] text-genesis-muted">
              {new Date(data.paid_at).toLocaleString(dateLocale)}
            </p>
          )}
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
          <Loader />
        </PublicPageShell>
      }
    >
      <OrderStatusContent />
    </Suspense>
  );
}
