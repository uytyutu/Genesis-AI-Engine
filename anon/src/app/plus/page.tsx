"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AnonSpeak } from "@/components/AnonSpeak";
import { useI18n } from "@/components/I18nProvider";
import { formatMoney, getProduct, type GiftSku } from "@/lib/pricing";

const PACKS: GiftSku[] = ["PACK_AI_PARTY", "PACK_SMART_BOTS", "PACK_ANON_PLUS"];

function PlusInner() {
  const { t, locale } = useI18n();
  const params = useSearchParams();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [ents, setEnts] = useState<string[]>([]);
  const [botLimit, setBotLimit] = useState(2);
  const unlocked = params.get("unlocked") === "1";

  useEffect(() => {
    fetch("/api/me/entitlements")
      .then((r) => r.json())
      .then((d) => {
        setEnts(d.entitlements || []);
        setBotLimit(d.botLimit || 2);
      })
      .catch(() => null);
  }, [unlocked]);

  async function buy(sku: GiftSku) {
    setBusy(sku);
    setError("");
    const r = await fetch("/api/packs/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sku }),
    });
    const d = await r.json();
    setBusy(null);
    if (!r.ok) {
      if (r.status === 401) {
        window.location.href = "/auth/login?next=/plus";
        return;
      }
      setError(d.error || t("error.generic"));
      return;
    }
    if (d.url) window.location.href = d.url;
  }

  return (
    <main className="anim-in mx-auto max-w-2xl space-y-6">
      <section className="text-center">
        <p className="text-xs tracking-[0.35em] text-violet-300">ANON+</p>
        <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">{t("plus.title")}</h1>
        <p className="mx-auto mt-3 max-w-md text-sm anon-muted">{t("plus.sub")}</p>
        <div className="mx-auto mt-4 max-w-md text-left">
          <AnonSpeak lineKey="veil.plus" mood="plus" accent="plus" size={64} />
        </div>
        {unlocked && (
          <p className="mt-3 rounded-2xl bg-emerald-500/15 px-4 py-2 text-sm text-emerald-200">
            {t("plus.unlocked")}
          </p>
        )}
      </section>

      <section className="anon-card space-y-3 p-5">
        <h2 className="font-semibold">{t("plus.freeTitle")}</h2>
        <ul className="space-y-2 text-sm anon-muted">
          <li>🎮 {t("plus.free.games")}</li>
          <li>👥 {t("plus.free.friends")}</li>
          <li>🤖 {t("plus.free.bots")}</li>
          <li>🏆 {t("plus.free.xp")}</li>
          <li>🔄 {t("plus.free.rematch")}</li>
        </ul>
        <p className="text-xs text-emerald-300/90">
          {t("plus.yourLimit", { n: botLimit })}
        </p>
      </section>

      <section className="overflow-hidden rounded-3xl border border-violet-400/30 bg-gradient-to-br from-violet-950/80 via-indigo-950/50 to-slate-950 p-6">
        <h2 className="text-2xl font-semibold">{t("plus.heroTitle")}</h2>
        <p className="mt-2 text-sm text-white/70">{t("plus.heroSub")}</p>
        <ul className="mt-4 space-y-2 text-sm">
          <li>🤖 {t("plus.feat.bots")}</li>
          <li>🧠 {t("plus.feat.smart")}</li>
          <li>🎭 {t("plus.feat.roles")}</li>
          <li>🎨 {t("plus.feat.themes")}</li>
          <li>✨ {t("plus.feat.create")}</li>
        </ul>
      </section>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-[0.2em] anon-muted">
          {t("plus.buyWhat")}
        </h2>
        {PACKS.map((sku) => {
          const p = getProduct(sku)!;
          const owned =
            (sku === "PACK_AI_PARTY" && (ents.includes("ai_party") || ents.includes("anon_plus"))) ||
            (sku === "PACK_SMART_BOTS" &&
              (ents.includes("smart_bots") || ents.includes("anon_plus"))) ||
            (sku === "PACK_ANON_PLUS" && ents.includes("anon_plus"));
          return (
            <article key={sku} className="anon-card flex flex-col gap-3 p-5 sm:flex-row sm:items-center">
              <div className="flex-1">
                <p className="text-2xl">{p.emoji}</p>
                <h3 className="font-semibold">{t(p.nameKey)}</h3>
                <p className="text-sm anon-muted">{t(p.descKey)}</p>
                <p className="mt-1 text-sm text-violet-200">
                  {formatMoney(p.amountCents, "eur", locale)}
                </p>
              </div>
              <button
                type="button"
                disabled={Boolean(busy) || owned}
                onClick={() => buy(sku)}
                className="anon-btn anon-btn-primary disabled:opacity-40"
              >
                {owned ? t("plus.owned") : busy === sku ? "…" : t("cta.getPack")}
              </button>
            </article>
          );
        })}
      </section>

      <p className="text-center text-xs anon-muted">{t("plus.note")}</p>
      <div className="flex justify-center gap-3">
        <Link href="/games" className="anon-btn anon-btn-primary">
          {t("cta.playNow")}
        </Link>
        <Link href="/create" className="anon-btn anon-btn-ghost">
          {t("cta.sendMoment")}
        </Link>
      </div>
    </main>
  );
}

export default function PlusPage() {
  return (
    <Suspense>
      <PlusInner />
    </Suspense>
  );
}
