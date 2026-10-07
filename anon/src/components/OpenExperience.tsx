"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AnonSpeak } from "./AnonSpeak";
import { useI18n } from "./I18nProvider";
import { DropExperience } from "./DropExperience";

type EngageView = {
  hintRequest: string;
  revealRequest: string;
  senderHint: string | null;
};

type GiftView = {
  id: string;
  type: string;
  theme: string;
  message: string;
  status: string;
  anonymous: boolean;
  publicAnonId: string | null;
  revealStatus: string;
  revealedName: string | null;
  openWhenLabel: string | null;
  easterClicks: number;
  media?: { kind?: string; mood?: string; engageHint?: string; clue?: string };
  engage?: EngageView;
};

export function OpenExperience({ token }: { token: string }) {
  const { t } = useI18n();
  const [phase, setPhase] = useState<"boot" | "ready" | "opened" | "error" | "locked" | "drop">(
    "boot"
  );
  const [gift, setGift] = useState<GiftView | null>(null);
  const [paidBySender, setPaidBySender] = useState(true);
  const [unlockAt, setUnlockAt] = useState<string | null>(null);
  const [tip, setTip] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [replied, setReplied] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [revealCount, setRevealCount] = useState<number | null>(null);
  const [consent, setConsent] = useState({ sender: false, recipient: false, ready: false });

  useEffect(() => {
    fetch(`/api/gifts/open/${token}`)
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || "fail");
        if (d.locked) {
          setUnlockAt(d.unlockAt);
          setPhase("locked");
          return;
        }
        setPaidBySender(d.paidBySender !== false);
        setGift(d.gift);
        if (d.gift?.status === "opened" || d.gift?.status === "replied") {
          setPhase("opened");
          return;
        }
        if (d.gift?.type === "SEND_DROP" || d.gift?.media?.kind === "drop") {
          setPhase("drop");
          return;
        }
        setPhase("ready");
      })
      .catch((e) => {
        setError(e.message || t("error.giftLost"));
        setPhase("error");
      });
  }, [token, t]);

  if (phase === "drop") {
    return <DropExperience token={token} />;
  }

  async function openGift() {
    const r = await fetch(`/api/gifts/open/${token}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "open" }),
    });
    const d = await r.json();
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    if (d.openedFast) setTip("fast");
    setPhase("opened");
  }

  async function easter() {
    const r = await fetch(`/api/gifts/open/${token}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "easter" }),
    });
    const d = await r.json();
    if (d.tip === "hey") setTip("hey");
    if (d.tip === "liked") setTip("liked");
  }

  async function sendReply() {
    setBusy(true);
    setError("");
    const r = await fetch(`/api/gifts/open/${token}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "reply", message: reply }),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    setThreadId(d.threadId);
    setReply("");
    setReplied(true);
  }

  async function startEngage(action: "ask_hint" | "ask_reveal") {
    if (!gift) return;
    setBusy(true);
    setError("");
    const r = await fetch(`/api/gifts/${gift.id}/engage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    const d = await r.json();
    if (r.status === 401) {
      setBusy(false);
      window.location.href = `/auth/login?next=/open/${token}`;
      return;
    }
    if (!r.ok) {
      setBusy(false);
      setError(d.error || t("error.generic"));
      return;
    }
    const pay = await fetch("/api/payments/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ orderId: d.orderId }),
    });
    const pd = await pay.json();
    setBusy(false);
    if (!pay.ok) {
      setError(pd.error || t("error.generic"));
      return;
    }
    if (pd.url) window.location.href = pd.url;
  }

  if (phase === "boot") {
    return (
      <main className="flex min-h-[70vh] items-center justify-center">
        <p className="anim-pulse text-violet-200">✨ {t("loading.pack")}</p>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="anon-card mx-auto mt-16 max-w-md p-8 text-center">
        <p className="text-3xl">😬</p>
        <p className="mt-4">{error || t("error.giftLost")}</p>
        <Link href="/" className="anon-btn anon-btn-primary mt-6 inline-flex">
          ANON
        </Link>
      </main>
    );
  }

  if (phase === "locked") {
    return (
      <main className="anon-card mx-auto mt-16 max-w-md p-8 text-center">
        <p className="text-4xl">🔒</p>
        <p className="mt-4 text-xl font-semibold">{t("openWhen.title")}</p>
        {unlockAt && (
          <p className="mt-2 text-sm anon-muted">
            {new Date(unlockAt).toLocaleString()}
          </p>
        )}
      </main>
    );
  }

  if (phase === "ready") {
    const clue =
      gift?.media && typeof gift.media === "object" && "clue" in gift.media
        ? String((gift.media as { clue?: string }).clue || "")
        : "";
    const isSecret =
      gift?.type === "SEND_SECRET" || gift?.type === "SEND_ANON" || gift?.anonymous;
    return (
      <main className="mx-auto flex min-h-[75vh] max-w-md flex-col items-center justify-center text-center">
        <div className="anim-in w-full rounded-3xl border border-violet-300/20 bg-gradient-to-br from-[#3d2a68] via-[#2a1848] to-[#1a1230] p-8">
          <p className="text-xs tracking-[0.35em] text-violet-200">
            {isSecret ? "🔐 SECRET" : "ANON"}
          </p>
          <h1 className="mt-6 text-3xl font-semibold sm:text-4xl">
            {isSecret ? t("secret.inboxCard") : t("open.forYou")}
          </h1>
          <p className="mt-4 anon-muted">{t("open.someone")}</p>
          {paidBySender && (
            <p className="mt-3 text-xs text-emerald-300/90">{t("open.paidBySender")}</p>
          )}
          {clue && (
            <p className="mt-4 rounded-2xl bg-[#2a1848]/70 px-4 py-3 text-sm">
              🧩 {t("secret.hintLabel")}: {clue}
            </p>
          )}
          {gift?.anonymous && gift.publicAnonId && !isSecret && (
            <p className="mt-6 text-sm text-fuchsia-300">
              🔒 From <strong>{gift.publicAnonId}</strong>
            </p>
          )}
          <button
            type="button"
            onClick={openGift}
            className="anon-btn anon-btn-primary mt-10 w-full px-10 text-base"
          >
            {t("cta.open")}
          </button>
        </div>
      </main>
    );
  }

  const engage = gift?.engage;
  const senderHint = engage?.senderHint || gift?.media?.engageHint || null;
  const hintPending = engage?.hintRequest === "pending";
  const revealPending = engage?.revealRequest === "pending";
  const revealAccepted = engage?.revealRequest === "accepted";
  const isAnon = Boolean(gift?.anonymous);

  return (
    <main className="mx-auto max-w-md space-y-5">
      {paidBySender && (
        <p className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-center text-xs text-emerald-200">
          {t("open.paidBySender")}
        </p>
      )}

      <button type="button" onClick={easter} className="anon-card anim-in w-full p-6 text-left">
        <p className="text-xs uppercase tracking-[0.25em] anon-muted">
          {gift?.type ? t(`gift.type.${gift.type}`) : ""}
        </p>
        {gift?.anonymous && (
          <p className="mt-2 text-sm text-fuchsia-300">
            {gift.revealStatus === "revealed" && gift.revealedName
              ? `🔓 ${gift.revealedName}`
              : gift.type === "SEND_SECRET"
                ? t("secrets.fromAnon")
                : gift.publicAnonId}
          </p>
        )}
        <p className="mt-4 whitespace-pre-wrap text-xl leading-relaxed">{gift?.message}</p>
      </button>

      {tip === "fast" && <p className="text-sm text-sky-300">{t("open.openedFast")}</p>}
      {tip === "hey" && <p className="text-sm text-violet-300">👀 {t("open.hey")}</p>}
      {tip === "liked" && <p className="text-sm text-pink-300">{t("open.liked")}</p>}

      {senderHint && (
        <section className="anon-card p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-violet-300">
            {t("open.clueFromThem")}
          </p>
          <p className="mt-2 text-sm">{senderHint}</p>
        </section>
      )}

      <section className="anon-card p-4">
        <AnonSpeak lineKey="veil.openReal" mood="curious" size={56} />
      </section>

      {/* A — Free reply primary */}
      <section className="anon-card space-y-3 border-violet-400/30 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">
          {t("open.freeBadge")}
        </p>
        <p className="font-semibold">{t("open.replyFree")}</p>
        <p className="text-sm anon-muted">{t("open.replyFreeSub")}</p>
        <textarea
          className="anon-input min-h-24"
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          placeholder={t("open.replyPh")}
          maxLength={2000}
        />
        <button
          type="button"
          disabled={busy}
          className="anon-btn anon-btn-primary w-full"
          onClick={sendReply}
        >
          💬 {t("cta.reply")}
        </button>
        {replied && <p className="text-sm text-emerald-300">{t("open.replySent")}</p>}
        {threadId && (
          <Link href={`/chat/${threadId}`} className="anon-btn anon-btn-ghost w-full">
            {t("open.chat")}
          </Link>
        )}
      </section>

      {/* B — Who are you? */}
      {isAnon && gift?.revealStatus !== "revealed" && (
        <section className="anon-card space-y-3 p-5">
          <p className="font-semibold">👀 {t("open.whoTitle")}</p>
          <p className="text-sm anon-muted">{t("open.whoSub")}</p>

          <div className="rounded-2xl bg-black/25 p-3 text-sm">
            <p className="font-medium">{t("open.stayMystery")}</p>
            <p className="mt-1 text-xs anon-muted">{t("open.stayMysterySub")}</p>
          </div>

          <button
            type="button"
            disabled={busy || hintPending || engage?.hintRequest === "answered"}
            className="anon-btn anon-btn-ghost w-full text-left"
            onClick={() => startEngage("ask_hint")}
          >
            <span className="flex w-full items-center justify-between gap-2">
              <span>
                💡 {t("open.askHint")}
                <span className="mt-1 block text-xs font-normal anon-muted">
                  {t("open.askHintGet")}
                </span>
              </span>
              <span className="shrink-0 text-xs text-violet-200">€0.99</span>
            </span>
          </button>
          {hintPending && (
            <p className="text-xs text-amber-200">{t("open.hintWaiting")}</p>
          )}

          <button
            type="button"
            disabled={
              busy ||
              revealPending ||
              revealAccepted ||
              engage?.revealRequest === "declined"
            }
            className="anon-btn anon-btn-ghost w-full text-left"
            onClick={() => startEngage("ask_reveal")}
          >
            <span className="flex w-full items-center justify-between gap-2">
              <span>
                🔓 {t("open.askReveal")}
                <span className="mt-1 block text-xs font-normal anon-muted">
                  {t("open.askRevealGet")}
                </span>
              </span>
              <span className="shrink-0 text-xs text-violet-200">€0.99</span>
            </span>
          </button>
          {revealPending && (
            <p className="text-xs text-amber-200">{t("open.revealWaiting")}</p>
          )}
          <p className="text-xs anon-muted">{t("open.askRevealNote")}</p>
        </section>
      )}

      {/* Mutual cinematic — only after both can proceed */}
      {isAnon && (revealAccepted || consent.ready) && gift?.revealStatus !== "revealed" && (
        <section className="anon-card mt-1 space-y-3 p-5 text-center">
          <p className="font-semibold">👀 {t("reveal.moment")}</p>
          <p className="text-xs anon-muted">{t("reveal.consentNeed")}</p>
          <button
            type="button"
            className="anon-btn anon-btn-ghost w-full"
            onClick={async () => {
              const r = await fetch(`/api/anonymous/${gift!.id}/reveal`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "consent" }),
              });
              const d = await r.json();
              if (!r.ok) {
                setError(d.error || t("error.generic"));
                return;
              }
              setConsent({
                sender: d.consent.sender,
                recipient: d.consent.recipient,
                ready: d.ready,
              });
            }}
          >
            {t("reveal.agree")}
          </button>
          <p className="text-xs anon-muted">
            {t("reveal.sender")}: {consent.sender ? "✓" : "…"} · {t("reveal.recipient")}:{" "}
            {consent.recipient ? "✓" : "…"}
          </p>
          {consent.ready && (
            <button
              type="button"
              className="anon-btn anon-btn-primary w-full"
              onClick={async () => {
                setRevealCount(3);
                for (const n of [3, 2, 1]) {
                  setRevealCount(n);
                  await new Promise((res) => setTimeout(res, 700));
                }
                const r = await fetch(`/api/anonymous/${gift!.id}/reveal`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ action: "checkout" }),
                });
                const d = await r.json();
                if (d.url) window.location.href = d.url;
                else if (d.revealed) window.location.reload();
                else setError(d.error || t("error.generic"));
                setRevealCount(null);
              }}
            >
              🔓 {t("reveal.paid")}
            </button>
          )}
          {revealCount != null && (
            <p className="text-4xl font-semibold anim-pulse">{revealCount}</p>
          )}
        </section>
      )}

      {gift?.anonymous && gift.revealStatus === "revealed" && gift.revealedName && (
        <section className="anon-card p-6 text-center">
          <p className="text-sm anon-muted">🔓 {t("reveal.moment")}</p>
          <p className="mt-3 text-2xl font-semibold">
            {t("reveal.thisWas", { name: gift.revealedName })} ❤️
          </p>
        </section>
      )}

      {/* C — Paid boost shelf */}
      <section className="anon-card space-y-3 p-5">
        <p className="font-semibold">{t("open.boostTitle")}</p>
        <p className="text-sm anon-muted">{t("open.boostSub")}</p>

        <div className="rounded-2xl border border-white/10 bg-black/20 p-3 opacity-70">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-sm font-medium">🎙 {t("open.boostVoice")}</p>
              <p className="mt-1 text-xs anon-muted">{t("open.boostVoiceGet")}</p>
            </div>
            <span className="text-xs text-amber-200">{t("open.coming")}</span>
          </div>
        </div>

        <Link
          href={`/moments?replyTo=${gift?.id || ""}`}
          className="flex items-center justify-between gap-2 rounded-2xl border border-white/10 bg-black/20 p-3 transition hover:border-white/25"
        >
          <div>
            <p className="text-sm font-medium">💌 {t("open.boostMoment")}</p>
            <p className="mt-1 text-xs anon-muted">{t("open.boostMomentGet")}</p>
          </div>
          <span className="shrink-0 text-xs text-violet-200">{t("open.createFor", { price: "€1.99" })}</span>
        </Link>

        <Link
          href={`/drop?replyTo=${gift?.id || ""}`}
          className="flex items-center justify-between gap-2 rounded-2xl border border-white/10 bg-black/20 p-3 transition hover:border-white/25"
        >
          <div>
            <p className="text-sm font-medium">🔥 {t("open.boostDrop")}</p>
            <p className="mt-1 text-xs anon-muted">{t("open.boostDropGet")}</p>
          </div>
          <span className="shrink-0 text-xs text-violet-200">{t("open.createFor", { price: "€1.99" })}</span>
        </Link>
      </section>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <section className="space-y-3 text-center pb-8">
        <Link href="/auth/register" className="text-sm anon-muted underline">
          {t("nav.register")}
        </Link>
      </section>
    </main>
  );
}
