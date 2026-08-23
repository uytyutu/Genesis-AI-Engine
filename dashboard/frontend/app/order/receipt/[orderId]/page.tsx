"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { PublicPageShell } from "../../../components/PublicPageShell";
import { Loader } from "../../../components/ui";
import { publicApiBase } from "../../../lib/publicApiBase";
import { dateLocaleForUi } from "../../../lib/locale/dateLocale";
import { isUiLocale } from "../../../lib/locale/types";
import { useLocale } from "../../../context/LocaleContext";

const API = publicApiBase();

type Party = {
  name?: string;
  address?: string;
  street?: string;
  zip_city?: string;
  country?: string;
  email?: string;
  vat_id?: string;
};

type ReceiptPayload = {
  brand: string;
  document_title?: string;
  order_id: string;
  customer: string;
  package: string;
  package_id?: string | null;
  amount: string;
  currency?: string;
  status: string;
  date?: string | null;
  service_date?: string | null;
  leistung?: string | null;
  seller?: Party | null;
  buyer?: Party | null;
  vat_note?: string | null;
  payment_mode?: string | null;
  download_available?: boolean;
  market_code?: string;
  ui_lang?: string;
};

type StatusBody = {
  ui_lang?: string | null;
  market_code?: string | null;
  receipt?: ReceiptPayload | null;
  client_receipt_text?: string;
  download_ready?: boolean;
  download_url?: string | null;
  paid?: boolean;
};

function ReceiptContent() {
  const { t, i18n } = useTranslation("site");
  const { applyUiLocale } = useLocale();
  const orderId = String(useParams().orderId ?? "");
  const [body, setBody] = useState<StatusBody | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [downloadError, setDownloadError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API}/api/sales/orders/${orderId}/status`);
        if (res.ok) {
          const json = (await res.json()) as StatusBody;
          if (!cancelled) setBody(json);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  useEffect(() => {
    const lang = body?.ui_lang;
    if (lang && isUiLocale(lang) && i18n.language !== lang) {
      applyUiLocale(lang);
    }
  }, [body?.ui_lang, applyUiLocale, i18n.language]);

  async function downloadZip() {
    setDownloadError("");
    setDownloadBusy(true);
    try {
      const url = `${API}${body?.download_url || `/api/sales/orders/${orderId}/download`}`;
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`Download fehlgeschlagen (${res.status})`);
      const blob = await res.blob();
      const cd = res.headers.get("content-disposition") || "";
      const match = /filename="?([^";]+)"?/i.exec(cd);
      const filename = match?.[1] || `virtus-site-${orderId}.zip`;
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : "Download fehlgeschlagen");
    } finally {
      setDownloadBusy(false);
    }
  }

  async function copyText() {
    if (!body?.client_receipt_text) return;
    try {
      await navigator.clipboard.writeText(body.client_receipt_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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

  const receipt = body?.receipt;
  if (!receipt || !body?.paid) {
    return (
      <PublicPageShell>
        <main className="mx-auto max-w-md py-12 text-center">
          <p className="text-genesis-muted">{t("order.status.notFound")}</p>
          <Link href={`/order/status/${orderId}`} className="mt-4 inline-block text-genesis-accent">
            ← {t("order.status.title")}
          </Link>
        </main>
      </PublicPageShell>
    );
  }

  const de = (body.ui_lang || receipt.ui_lang || i18n.language) === "de" || body.market_code === "DE";
  const dateLocale = dateLocaleForUi(i18n.language);
  const when = receipt.date ? new Date(receipt.date).toLocaleString(dateLocale) : "—";
  const serviceWhen = receipt.service_date
    ? new Date(receipt.service_date).toLocaleDateString(dateLocale)
    : when;

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-lg py-8">
        <article className="rounded-3xl border border-genesis-border-subtle bg-white px-8 py-10 text-slate-900 shadow-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            {receipt.brand}
          </p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">
            {receipt.document_title || (de ? "Rechnung / Zahlungsbeleg" : t("order.status.viewReceipt"))}
          </h1>
          {de ? (
            <p className="mt-1 text-xs text-slate-500">Angaben gemäß § 14 UStG — bitte prüfen</p>
          ) : null}

          <dl className="mt-8 space-y-4 text-sm">
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{de ? "Rechnungsnummer" : t("order.status.yourOrder")}</dt>
              <dd className="font-mono font-medium">{receipt.order_id}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{de ? "Rechnungsdatum" : "Date"}</dt>
              <dd className="text-right text-slate-700">{when}</dd>
            </div>
            {de ? (
              <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
                <dt className="text-slate-500">Leistungsdatum</dt>
                <dd className="text-right text-slate-700">{serviceWhen}</dd>
              </div>
            ) : null}

            {receipt.seller ? (
              <div className="border-b border-slate-200 pb-3">
                <dt className="text-slate-500">{de ? "Verkäufer" : "Seller"}</dt>
                <dd className="mt-1 space-y-0.5 text-right text-slate-800">
                  <p className="font-medium">{receipt.seller.name}</p>
                  {receipt.seller.address ? <p>{receipt.seller.address}</p> : null}
                  {receipt.seller.email ? <p>{receipt.seller.email}</p> : null}
                </dd>
              </div>
            ) : null}

            <div className="border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{de ? "Kunde / Rechnungsempfänger" : "Customer"}</dt>
              <dd className="mt-1 space-y-0.5 text-right font-medium">
                <p>{receipt.buyer?.name || receipt.customer}</p>
                {receipt.buyer?.street ? <p className="font-normal">{receipt.buyer.street}</p> : null}
                {receipt.buyer?.zip_city ? (
                  <p className="font-normal">{receipt.buyer.zip_city}</p>
                ) : null}
                {receipt.buyer?.country ? (
                  <p className="font-normal">{receipt.buyer.country}</p>
                ) : null}
                {receipt.buyer?.email ? (
                  <p className="font-normal text-slate-600">{receipt.buyer.email}</p>
                ) : null}
              </dd>
            </div>

            <div className="border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{de ? "Leistungsbeschreibung" : "Package"}</dt>
              <dd className="text-right font-medium">
                {receipt.leistung || receipt.package}
              </dd>
            </div>

            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{de ? "Gesamtbetrag" : "Amount"}</dt>
              <dd className="text-right text-lg font-semibold">{receipt.amount}</dd>
            </div>

            {receipt.vat_note ? (
              <div className="border-b border-slate-200 pb-3">
                <dt className="text-slate-500">{de ? "MwSt. / Hinweis" : "VAT"}</dt>
                <dd className="text-right text-xs leading-relaxed text-slate-600">
                  {receipt.vat_note}
                </dd>
              </div>
            ) : null}

            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{t("order.status.status")}</dt>
              <dd className="font-medium text-emerald-700">{receipt.status}</dd>
            </div>

            {receipt.payment_mode ? (
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">{de ? "Zahlungsart" : "Payment"}</dt>
                <dd className="text-right text-slate-700">{receipt.payment_mode}</dd>
              </div>
            ) : null}
          </dl>

          {receipt.download_available && body.download_url ? (
            <button
              type="button"
              disabled={downloadBusy}
              onClick={() => void downloadZip()}
              className="mt-8 flex w-full items-center justify-center rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {downloadBusy ? "Wird geladen…" : t("order.status.downloadZip")}
            </button>
          ) : null}
          {downloadError ? <p className="mt-2 text-center text-xs text-rose-600">{downloadError}</p> : null}

          {body.client_receipt_text ? (
            <button
              type="button"
              onClick={() => void copyText()}
              className="mt-3 flex w-full items-center justify-center rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              {copied
                ? de
                  ? "Kopiert"
                  : "Copied"
                : de
                  ? "Rechnungstext kopieren"
                  : "Copy receipt text"}
            </button>
          ) : null}
        </article>

        <div className="mt-6 flex justify-center gap-4 text-sm">
          <Link href={`/order/status/${orderId}`} className="text-genesis-accent hover:underline">
            ← {t("order.status.title")}
          </Link>
          <Link href="/order/history" className="text-genesis-muted hover:underline">
            {t("order.status.orderHistory")}
          </Link>
        </div>
      </main>
    </PublicPageShell>
  );
}

export default function OrderReceiptPage() {
  return (
    <Suspense
      fallback={
        <PublicPageShell>
          <Loader />
        </PublicPageShell>
      }
    >
      <ReceiptContent />
    </Suspense>
  );
}
