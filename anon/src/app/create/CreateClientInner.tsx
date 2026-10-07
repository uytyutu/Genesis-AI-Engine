"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/components/I18nProvider";
import { THEMES } from "@/lib/pricing";

type Product = {
  sku: string;
  pillar: string;
  emoji: string;
  amountCents: number;
  priceLabel: string;
  nameKey: string;
  descKey: string;
};

export default function CreateClientInner() {
  const { t } = useI18n();
  const router = useRouter();
  const params = useSearchParams();
  const pillar = params.get("pillar") || "send";
  const [step, setStep] = useState(1);
  const [products, setProducts] = useState<Product[]>([]);
  const [sku, setSku] = useState("SEND_MOMENT");
  const [message, setMessage] = useState("");
  const [recipient, setRecipient] = useState("");
  const [theme, setTheme] = useState<(typeof THEMES)[number]>("dream");
  const [anonymous, setAnonymous] = useState(pillar === "anon");
  const [openWhen, setOpenWhen] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loadingLabel, setLoadingLabel] = useState("");

  useEffect(() => {
    fetch("/api/products")
      .then((r) => r.json())
      .then((d) => setProducts(d.products || []));
  }, []);

  useEffect(() => {
    if (pillar === "anon") {
      setSku("SEND_ANON");
      setAnonymous(true);
    } else if (pillar === "open_when") {
      setSku("SEND_OPEN_WHEN");
    }
  }, [pillar]);

  const filtered = useMemo(() => {
    if (pillar === "anon") return products.filter((p) => p.pillar === "anon");
    if (pillar === "open_when") return products.filter((p) => p.pillar === "open_when");
    return products.filter((p) => p.pillar === "send");
  }, [products, pillar]);

  const selected = products.find((p) => p.sku === sku) || filtered[0];

  async function checkout() {
    setError("");
    setBusy(true);
    setLoadingLabel(t("loading.pack"));
    try {
      const me = await fetch("/api/auth/me");
      if (!me.ok) {
        router.push("/auth/register?next=/create");
        return;
      }
      setLoadingLabel(anonymous ? t("loading.hide") : t("loading.lock"));
      const create = await fetch("/api/gifts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: selected?.sku || sku,
          message,
          recipientLabel: recipient,
          theme,
          anonymous: anonymous || selected?.pillar === "anon",
          openWhenLabel: openWhen || undefined,
        }),
      });
      const created = await create.json();
      if (!create.ok) throw new Error(created.error || "Create failed");

      const pay = await fetch("/api/payments/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orderId: created.orderId }),
      });
      const paid = await pay.json();
      if (!pay.ok) throw new Error(paid.error || "Checkout failed");

      if (paid.url) {
        window.location.href = paid.url;
        return;
      }
      router.push(paid.sharePath || "/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error.generic"));
    } finally {
      setBusy(false);
      setLoadingLabel("");
    }
  }

  return (
    <main className="anim-in">
      <h1 className="mb-2 text-2xl font-semibold">{t("cta.sendMoment")}</h1>
      <p className="mb-6 text-sm anon-muted">
        {t("creator.step1")} → {t("creator.step6")}
      </p>

      <div className="mb-4 flex gap-2 overflow-x-auto text-xs">
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setStep(n)}
            className={`rounded-full px-3 py-1 ${
              step === n ? "bg-violet-500/30 text-white" : "bg-white/5 anon-muted"
            }`}
          >
            {n}
          </button>
        ))}
      </div>

      {step === 1 && (
        <div className="anon-card space-y-3 p-5">
          <p className="font-medium">{t("creator.step1")}</p>
          <div className="grid grid-cols-2 gap-2">
            {["❤️", "😂", "🥺", "🔥", "🤫", "🎁"].map((e) => (
              <button
                key={e}
                type="button"
                className="anon-btn anon-btn-ghost text-2xl"
                onClick={() => setStep(2)}
              >
                {e}
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-3">
          {(filtered.length ? filtered : products).map((p) => (
            <button
              key={p.sku}
              type="button"
              onClick={() => {
                setSku(p.sku);
                setAnonymous(p.pillar === "anon");
                setStep(3);
              }}
              className={`anon-card flex w-full items-start gap-4 p-5 text-left transition hover:border-white/20 ${
                sku === p.sku ? "ring-2 ring-violet-400/50" : ""
              }`}
            >
              <span className="text-3xl">{p.emoji}</span>
              <span>
                <span className="block font-semibold">{t(p.nameKey)}</span>
                <span className="block text-sm anon-muted">{t(p.descKey)}</span>
                <span className="mt-2 inline-block text-sm text-sky-300">{p.priceLabel}</span>
              </span>
            </button>
          ))}
        </div>
      )}

      {step === 3 && (
        <div className="anon-card space-y-4 p-5">
          <label className="block text-sm">
            {t("creator.message")}
            <textarea
              className="anon-input mt-2 min-h-32"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="…"
              maxLength={4000}
            />
          </label>
          <label className="block text-sm">
            {t("creator.theme")}
            <select
              className="anon-input mt-2"
              value={theme}
              onChange={(e) => setTheme(e.target.value as typeof theme)}
            >
              {THEMES.map((th) => (
                <option key={th} value={th}>
                  {th}
                </option>
              ))}
            </select>
          </label>
          {(sku === "SEND_ANON" || pillar === "anon") && (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={anonymous}
                onChange={(e) => setAnonymous(e.target.checked)}
              />
              🕵️ {t("creator.stayAnon")}
            </label>
          )}
          {(sku === "SEND_OPEN_WHEN" || pillar === "open_when") && (
            <label className="block text-sm">
              {t("creator.openWhen")}
              <input
                className="anon-input mt-2"
                value={openWhen}
                onChange={(e) => setOpenWhen(e.target.value)}
              />
            </label>
          )}
          <button
            type="button"
            className="anon-btn anon-btn-primary w-full"
            onClick={() => setStep(4)}
          >
            {t("creator.next")}
          </button>
        </div>
      )}

      {step === 4 && (
        <div className="anon-card space-y-4 p-5">
          <label className="block text-sm">
            {t("creator.recipient")}
            <input
              className="anon-input mt-2"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder="Alex"
            />
          </label>
          <button
            type="button"
            className="anon-btn anon-btn-primary w-full"
            onClick={() => setStep(5)}
          >
            {t("creator.preview")}
          </button>
        </div>
      )}

      {step >= 5 && (
        <div className="space-y-4">
          <div className="anon-card p-6">
            <p className="text-xs uppercase tracking-[0.25em] anon-muted">
              {t("creator.preview")}
            </p>
            <p className="mt-3 text-2xl">{selected?.emoji || "💌"}</p>
            <p className="mt-2 text-lg font-semibold">
              {recipient ? t("creator.for", { name: recipient }) : t("open.forYou")}
            </p>
            <p className="mt-4 whitespace-pre-wrap text-base leading-relaxed">
              {message || "…"}
            </p>
            {anonymous && <p className="mt-4 text-sm text-fuchsia-300">🕵️ ANON #•••••</p>}
            {openWhen && (
              <p className="mt-2 text-sm text-sky-300">
                🔒 {t("creator.openWhen")} {openWhen}
              </p>
            )}
          </div>
          {error && <p className="text-sm text-rose-300">{error}</p>}
          {busy && <p className="anim-pulse text-sm text-violet-200">{loadingLabel}</p>}
          <button
            type="button"
            disabled={busy || !message.trim()}
            className="anon-btn anon-btn-primary w-full disabled:opacity-50"
            onClick={checkout}
          >
            {t("cta.checkout")} · {selected?.priceLabel || "€0.99"}
          </button>
        </div>
      )}
    </main>
  );
}
