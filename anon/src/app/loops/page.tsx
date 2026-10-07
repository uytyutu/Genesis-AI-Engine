"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useI18n } from "@/components/I18nProvider";
import {
  LOOP_HUB,
  SAY_INTENTS,
  WHEN_TRIGGERS,
  type ViralKind,
} from "@/lib/viral/catalog";

function LoopStatusBadge({
  live,
  guessViaSecrets,
}: {
  live: boolean;
  guessViaSecrets?: boolean;
}) {
  const { t } = useI18n();
  const label = live
    ? guessViaSecrets
      ? t("loops.guessViaSecrets")
      : t("loops.honestLive")
    : t("loops.honestSoon");
  const cls = live
    ? "bg-emerald-500/15 text-emerald-200"
    : "bg-white/10 text-white/55";
  return (
    <span
      className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] ${cls}`}
    >
      {label}
    </span>
  );
}

export default function LoopsPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [sayIntent, setSayIntent] = useState("miss");
  const [whenTrigger, setWhenTrigger] = useState("need_it");
  const [message, setMessage] = useState("");

  async function create(kind: ViralKind, config?: Record<string, unknown>) {
    setBusy(kind);
    setErr("");
    try {
      const r = await fetch("/api/viral", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, config }),
      });
      const d = await r.json();
      if (!r.ok) {
        if (r.status === 401) {
          router.push(`/auth/login?next=/loops`);
          return;
        }
        setErr(d.error || t("leave.errorCreate"));
        return;
      }
      if (d.redirect) {
        router.push(d.redirect);
        return;
      }
      if (d.checkoutUrl) {
        window.location.href = d.checkoutUrl;
        return;
      }
      if (d.space?.sharePath) {
        router.push(d.space.path);
      }
    } finally {
      setBusy(null);
    }
  }

  const alreadyParts = t("leave.alreadyLink", {
    inbox: "__INBOX__",
    cabinet: "__CABINET__",
  });
  const [alreadyBefore, alreadyAfter = ""] = alreadyParts.split("__INBOX__");
  const [alreadyMid, alreadyTail = ""] = alreadyAfter.split("__CABINET__");

  return (
    <main className="anim-in mx-auto max-w-lg space-y-6 pb-10">
      <header className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-violet-300/90">
          {t("leave.eyebrow")}
        </p>
        <h1 className="mt-3 text-3xl font-semibold">{t("leave.title")}</h1>
        <p className="mt-3 text-sm anon-muted">{t("leave.sub")}</p>
      </header>

      {err && <p className="text-center text-sm text-rose-300">{err}</p>}

      <div className="space-y-3">
        {LOOP_HUB.map((item) => (
          <article key={item.kind} className="anon-card p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-2xl">{item.emoji}</p>
                  <LoopStatusBadge live={item.live} guessViaSecrets={item.kind === "guess"} />
                </div>
                <h2 className="mt-2 text-lg font-semibold">{t(item.titleKey)}</h2>
                <p className="mt-1 text-sm anon-muted">{t(item.blurbKey)}</p>
                <p className="mt-2 text-xs text-violet-200">{t(item.priceLabelKey)}</p>
              </div>
            </div>

            {item.kind === "say" && (
              <div className="mt-4 space-y-2">
                <select
                  className="anon-input"
                  value={sayIntent}
                  onChange={(e) => setSayIntent(e.target.value)}
                >
                  {SAY_INTENTS.map((i) => (
                    <option key={i.id} value={i.id}>
                      {t(i.labelKey)}
                    </option>
                  ))}
                </select>
                <textarea
                  className="anon-input min-h-20"
                  placeholder={t("leave.optionalNote")}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>
            )}

            {item.kind === "when" && (
              <div className="mt-4 space-y-2">
                <select
                  className="anon-input"
                  value={whenTrigger}
                  onChange={(e) => setWhenTrigger(e.target.value)}
                >
                  {WHEN_TRIGGERS.map((i) => (
                    <option key={i.id} value={i.id}>
                      {t(i.labelKey)}
                    </option>
                  ))}
                </select>
                <textarea
                  className="anon-input min-h-20"
                  placeholder={t("leave.yourMessage")}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>
            )}

            <button
              type="button"
              className="anon-btn anon-btn-primary mt-4 w-full"
              disabled={busy === item.kind}
              onClick={() => {
                if (item.kind === "say") {
                  create("say", { intent: sayIntent, message });
                } else if (item.kind === "when") {
                  create("when", { trigger: whenTrigger, message });
                } else if (item.kind === "guess") {
                  create("guess");
                } else {
                  create(item.kind);
                }
              }}
            >
              {busy === item.kind
                ? t("leave.busy")
                : item.kind === "guess"
                  ? t("leave.openSecrets")
                  : t("leave.createLink")}
            </button>
          </article>
        ))}
      </div>

      <p className="text-center text-xs anon-muted">
        {alreadyBefore}
        <Link href="/inbox" className="underline">
          {t("leave.alreadyInbox")}
        </Link>
        {alreadyMid}
        <Link href="/dashboard" className="underline">
          {t("leave.alreadyCabinet")}
        </Link>
        {alreadyTail}
      </p>
    </main>
  );
}
