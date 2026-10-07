"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AnonSpeak } from "@/components/AnonSpeak";
import { useI18n } from "@/components/I18nProvider";
import { formatMoney, type DropMood } from "@/lib/pricing";
import { moodToTheme, THEME_TOKENS } from "@/lib/themes";

const MOODS: DropMood[] = [
  "sweet",
  "funny",
  "suspicious",
  "savage",
  "secret",
  "beautiful",
  "unexpected",
];

const MOOD_EMOJI: Record<string, string> = {
  sweet: "💜",
  funny: "😂",
  suspicious: "👀",
  savage: "🔥",
  secret: "🕵️",
  beautiful: "✨",
  unexpected: "🤯",
};

export default function DropCreatePage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [mood, setMood] = useState<DropMood>("secret");
  const [message, setMessage] = useState("");
  const [recipient, setRecipient] = useState("");
  const [anonymous, setAnonymous] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const theme = THEME_TOKENS[moodToTheme(mood)];

  async function checkout() {
    setError("");
    if (message.trim().length < 1) {
      setError(t("drop.needMessage"));
      return;
    }
    setBusy(true);
    try {
      const me = await fetch("/api/auth/me");
      if (!me.ok) {
        router.push("/auth/register?next=/drop");
        return;
      }
      const create = await fetch("/api/gifts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "SEND_DROP",
          message,
          recipientLabel: recipient,
          mood,
          anonymous,
        }),
      });
      const created = await create.json();
      if (!create.ok) throw new Error(created.error || t("error.generic"));

      const pay = await fetch("/api/payments/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orderId: created.orderId }),
      });
      const paid = await pay.json();
      if (!pay.ok) throw new Error(paid.error || t("error.generic"));
      if (paid.url) {
        window.location.href = paid.url;
        return;
      }
      router.push(paid.sharePath || "/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error.generic"));
    } finally {
      setBusy(false);
    }
  }

  const price = formatMoney(199, "eur", locale);

  return (
    <main className="anim-in mx-auto max-w-lg space-y-6">
      <section className="text-center">
        <p className="text-xs tracking-[0.35em] text-violet-300">🔥 SECRET DROP</p>
        <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">{t("drop.createTitle")}</h1>
        <p className="mx-auto mt-3 max-w-md text-sm anon-muted">{t("drop.createSub")}</p>
        <p className="mt-2 text-xs text-white/70">{t("drop.includes")}</p>
        <p className="mt-3 text-lg font-semibold text-violet-100">{price}</p>
      </section>

      <section className="anon-card p-4">
        <AnonSpeak lineKey="veil.drop" mood="drop" accent="drop" size={72} />
      </section>

      <section className="anon-card space-y-3 p-5 text-left text-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-fuchsia-300">
          {t("offer.recipientGets")}
        </p>
        <ul className="space-y-2 anon-muted">
          <li>🔒 {t("offer.drop.r1")}</li>
          <li>✨ {t("offer.drop.r2")}</li>
          <li>💌 {t("offer.drop.r3")}</li>
          <li>🕵️ {t("offer.drop.r4")}</li>
        </ul>
        <p className="pt-1 text-xs">
          <span className="anon-muted">{t("offer.youGet")} </span>
          {t("offer.drop.g1")} · {t("offer.drop.g2")}
        </p>
        <p className="text-xs">
          <span className="anon-muted">{t("offer.forWhom")} </span>
          {t("offer.drop.for")}
        </p>
      </section>

      <section
        className={`rounded-3xl border border-white/10 bg-gradient-to-br p-5 ${theme.gradient}`}
      >
        <p className="text-xs uppercase tracking-[0.2em] anon-muted">{t("drop.pickMood")}</p>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {MOODS.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMood(m)}
              className={`rounded-2xl px-3 py-3 text-left text-sm transition ${
                mood === m
                  ? "bg-white/20 ring-2 ring-white/40"
                  : "bg-black/25 hover:bg-black/40"
              }`}
            >
              <span className="text-lg">{MOOD_EMOJI[m]}</span>
              <div className="mt-1 font-semibold">{t(`drop.mood.${m}`)}</div>
            </button>
          ))}
        </div>
      </section>

      <section className="anon-card space-y-3 p-5">
        <label className="block text-sm">
          <span className="anon-muted">{t("drop.forWho")}</span>
          <input
            className="anon-input mt-1"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder={t("drop.forWhoPh")}
          />
        </label>
        <label className="block text-sm">
          <span className="anon-muted">{t("drop.inside")}</span>
          <textarea
            className="anon-input mt-1 min-h-28"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t("drop.insidePh")}
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={anonymous}
            onChange={(e) => setAnonymous(e.target.checked)}
          />
          {t("drop.sendAnon")}
        </label>
      </section>

      <section
        className={`rounded-3xl border border-white/10 bg-gradient-to-br p-6 text-center ${theme.gradient}`}
      >
        <p className="text-xs tracking-[0.3em]" style={{ color: theme.accent }}>
          PREVIEW
        </p>
        <p className="mt-3 text-lg font-semibold">{t("drop.someoneSent")}</p>
        <p className="mt-2 text-sm text-white/70">{t("drop.dontOpen")}</p>
        <p className="mt-4 text-xs anon-muted">{t(`drop.mood.${mood}`)}</p>
      </section>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <button
        type="button"
        disabled={busy}
        onClick={checkout}
        className="anon-btn anon-btn-primary w-full text-base disabled:opacity-50"
      >
        {busy ? "…" : t("offer.drop.ctaPrice", { price })}
      </button>
      <p className="text-center text-xs anon-muted">{t("offer.afterPay")}</p>

      <p className="text-center text-xs anon-muted">{t("drop.viralHint")}</p>
      <div className="flex justify-center gap-3 text-sm">
        <Link href="/moments" className="underline anon-muted">
          {t("nav.moments")}
        </Link>
        <Link href="/plus" className="underline anon-muted">
          ANON+
        </Link>
      </div>
    </main>
  );
}
