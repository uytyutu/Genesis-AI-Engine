"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import QRCode from "qrcode";
import { useI18n } from "@/components/I18nProvider";

function SuccessInner() {
  const { t } = useI18n();
  const params = useSearchParams();
  const orderId = params.get("order_id");
  const sessionId = params.get("session_id");
  const sandbox = params.get("sandbox") === "1";
  const engageParam = params.get("engage") === "1";
  const [sharePath, setSharePath] = useState<string | null>(null);
  const [engage, setEngage] = useState(engageParam);
  const [qr, setQr] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!orderId) return;
    (async () => {
      const r = await fetch(`/api/orders/${orderId}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, sandbox }),
      });
      const d = await r.json();
      if (!r.ok) {
        setError(d.error || t("error.generic"));
        return;
      }
      if (d.engage) setEngage(true);
      setSharePath(d.sharePath);
      if (d.sharePath && !d.engage) {
        const url = `${window.location.origin}${d.sharePath}`;
        setQr(await QRCode.toDataURL(url, { margin: 1, width: 220 }));
      }
    })();
  }, [orderId, sessionId, sandbox, t]);

  const fullUrl =
    typeof window !== "undefined" && sharePath
      ? `${window.location.origin}${sharePath}`
      : "";

  async function copy() {
    if (!fullUrl) return;
    await navigator.clipboard.writeText(fullUrl);
  }

  function wa() {
    const text = encodeURIComponent(`💌 I sent you something.\n\nOpen:\n${fullUrl}`);
    window.open(`https://wa.me/?text=${text}`, "_blank");
  }

  function tg() {
    const text = encodeURIComponent(`💌 I sent you something.\n${fullUrl}`);
    window.open(
      `https://t.me/share/url?url=${encodeURIComponent(fullUrl)}&text=${text}`,
      "_blank"
    );
  }

  async function nativeShare() {
    if (navigator.share && fullUrl) {
      await navigator.share({ title: "ANON", text: "💌 I sent you something.", url: fullUrl });
    }
  }

  if (engage) {
    return (
      <main className="anon-card mx-auto max-w-md p-6 text-center">
        <p className="text-4xl">✨</p>
        <h1 className="mt-4 text-2xl font-semibold">{t("success.engage")}</h1>
        <p className="mt-2 anon-muted">{t("success.engageSub")}</p>
        {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
        {sharePath && (
          <Link href={sharePath} className="anon-btn anon-btn-primary mt-6 w-full">
            {t("cta.open")}
          </Link>
        )}
        <Link href="/dashboard" className="anon-btn anon-btn-ghost mt-3 w-full">
          {t("nav.cabinet")}
        </Link>
      </main>
    );
  }

  return (
    <main className="anon-card mx-auto max-w-md p-6 text-center">
      <p className="text-4xl">💌</p>
      <h1 className="mt-4 text-2xl font-semibold">{t("success.sent")}</h1>
      <p className="mt-2 anon-muted">{t("share.ready")}</p>
      {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
      {sharePath && (
        <>
          <div className="mt-6 grid gap-2">
            <button type="button" className="anon-btn anon-btn-primary" onClick={wa}>
              🟢 {t("share.whatsapp")}
            </button>
            <button type="button" className="anon-btn anon-btn-ghost" onClick={tg}>
              🔵 {t("share.telegram")}
            </button>
            <button type="button" className="anon-btn anon-btn-ghost" onClick={copy}>
              📋 {t("share.copy")}
            </button>
            <button type="button" className="anon-btn anon-btn-ghost" onClick={nativeShare}>
              📱 {t("share.native")}
            </button>
          </div>
          {qr && (
            <div className="mt-8">
              <p className="mb-3 text-sm anon-muted">{t("share.qr")}</p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={qr} alt="Gift QR" className="mx-auto rounded-xl bg-white p-2" />
            </div>
          )}
          <Link href={sharePath} className="mt-6 inline-block text-sm text-sky-300 underline">
            {t("share.preview")}
          </Link>
        </>
      )}
      <Link href="/dashboard" className="anon-btn anon-btn-ghost mt-6 w-full">
        {t("nav.cabinet")}
      </Link>
    </main>
  );
}

export default function SuccessPage() {
  return (
    <Suspense>
      <SuccessInner />
    </Suspense>
  );
}
