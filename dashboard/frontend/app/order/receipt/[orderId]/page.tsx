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

type ReceiptPayload = {
  brand: string;
  order_id: string;
  customer: string;
  package: string;
  package_id?: string | null;
  amount: string;
  currency?: string;
  status: string;
  date?: string | null;
  download_available?: boolean;
  market_code?: string;
};

type StatusBody = {
  ui_lang?: string | null;
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

  const dateLocale = dateLocaleForUi(i18n.language);
  const when = receipt.date ? new Date(receipt.date).toLocaleString(dateLocale) : "—";

  return (
    <PublicPageShell>
      <main className="mx-auto max-w-md py-8">
        <article className="rounded-3xl border border-genesis-border-subtle bg-white px-8 py-10 text-slate-900 shadow-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            {receipt.brand}
          </p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">{t("order.status.viewReceipt")}</h1>

          <dl className="mt-8 space-y-4 text-sm">
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{t("order.status.yourOrder")}</dt>
              <dd className="font-mono font-medium">{receipt.order_id}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Customer</dt>
              <dd className="text-right font-medium">{receipt.customer}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Package</dt>
              <dd className="text-right font-medium">{receipt.package}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">Amount</dt>
              <dd className="text-right text-lg font-semibold">{receipt.amount}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-200 pb-3">
              <dt className="text-slate-500">{t("order.status.status")}</dt>
              <dd className="font-medium text-emerald-700">{receipt.status}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Date</dt>
              <dd className="text-right text-slate-700">{when}</dd>
            </div>
          </dl>

          {receipt.download_available && body.download_url && (
            <a
              href={`${API}${body.download_url}`}
              className="mt-8 flex w-full items-center justify-center rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800"
            >
              {t("order.status.downloadZip")}
            </a>
          )}
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
