"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useI18n } from "./I18nProvider";
import { moodToTheme, THEME_TOKENS } from "@/lib/themes";

type GiftView = {
  id: string;
  type: string;
  theme: string;
  message: string;
  media?: { mood?: string; kind?: string };
  anonymous?: boolean;
  publicAnonId?: string | null;
};

type Phase =
  | "boot"
  | "tease"
  | "door"
  | "card"
  | "pulse"
  | "unlocked"
  | "error";

const DOORS = ["🚪", "🚪", "🚪"];
const CARDS = ["💜", "👀", "🔥"];

export function DropExperience({ token }: { token: string }) {
  const { t } = useI18n();
  const [phase, setPhase] = useState<Phase>("boot");
  const [gift, setGift] = useState<GiftView | null>(null);
  const [error, setError] = useState("");
  const [stepPick, setStepPick] = useState<number | null>(null);

  const mood = gift?.media?.mood || "secret";
  const theme = THEME_TOKENS[moodToTheme(mood)];

  useEffect(() => {
    fetch(`/api/gifts/open/${token}`)
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || "fail");
        setGift(d.gift);
        setPhase("tease");
      })
      .catch((e) => {
        setError(e.message || t("error.giftLost"));
        setPhase("error");
      });
  }, [token, t]);

  async function markOpened() {
    await fetch(`/api/gifts/open/${token}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "open" }),
    });
  }

  if (phase === "boot") {
    return (
      <main className="flex min-h-[70vh] items-center justify-center">
        <p className="anim-pulse text-violet-200">✨ {t("drop.loading")}</p>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="anon-card mx-auto mt-16 max-w-md p-8 text-center">
        <p className="text-3xl">😬</p>
        <p className="mt-4">{error}</p>
        <Link href="/" className="anon-btn anon-btn-primary mt-6 inline-flex">
          ANON
        </Link>
      </main>
    );
  }

  return (
    <main
      className={`mx-auto flex min-h-[78vh] max-w-md flex-col items-center justify-center px-2 text-center`}
    >
      <div
        className={`w-full rounded-[2rem] border border-white/10 bg-gradient-to-br p-8 shadow-2xl ${theme.gradient}`}
        style={{ boxShadow: `0 0 60px ${theme.glow}` }}
      >
        {phase === "tease" && (
          <div className="anim-in space-y-5">
            <p className="text-xs tracking-[0.35em]" style={{ color: theme.accent }}>
              ANON DROP
            </p>
            <h1 className="text-3xl font-semibold">{t("drop.someoneSent")}</h1>
            <p className="text-lg font-medium text-white/80">{t("drop.dontOpen")}</p>
            <p className="text-sm anon-muted">{t(`drop.mood.${mood}`)}</p>
            <button
              type="button"
              className="anon-btn anon-btn-primary mt-4 w-full text-base"
              onClick={() => setPhase("door")}
            >
              {t("drop.openAnyway")}
            </button>
          </div>
        )}

        {phase === "door" && (
          <div className="anim-in space-y-5">
            <p className="text-xs uppercase tracking-[0.25em] anon-muted">
              {t("drop.step", { n: 1, max: 3 })}
            </p>
            <h2 className="text-2xl font-semibold">{t("drop.pickDoor")}</h2>
            <div className="grid grid-cols-3 gap-3">
              {DOORS.map((d, i) => (
                <button
                  key={i}
                  type="button"
                  className="rounded-2xl bg-black/30 py-8 text-4xl transition hover:scale-105 hover:bg-black/50"
                  onClick={() => {
                    setStepPick(i);
                    setTimeout(() => setPhase("card"), 350);
                  }}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        )}

        {phase === "card" && (
          <div className="anim-in space-y-5">
            <p className="text-xs uppercase tracking-[0.25em] anon-muted">
              {t("drop.step", { n: 2, max: 3 })}
            </p>
            <h2 className="text-2xl font-semibold">{t("drop.pickCard")}</h2>
            <div className="grid grid-cols-3 gap-3">
              {CARDS.map((c, i) => (
                <button
                  key={i}
                  type="button"
                  className="rounded-2xl bg-black/30 py-8 text-4xl transition hover:scale-105 hover:bg-black/50"
                  onClick={() => {
                    setStepPick(i);
                    setTimeout(() => setPhase("pulse"), 300);
                  }}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        )}

        {phase === "pulse" && (
          <div className="anim-in space-y-6 py-8">
            <p className="text-xs uppercase tracking-[0.25em] anon-muted">
              {t("drop.step", { n: 3, max: 3 })}
            </p>
            <p className="anim-pulse text-5xl">✨</p>
            <p className="text-xl font-semibold">{t("drop.unlocking")}</p>
            <button
              type="button"
              className="anon-btn anon-btn-primary w-full"
              onClick={async () => {
                await markOpened();
                setPhase("unlocked");
              }}
            >
              {t("drop.unlock")}
            </button>
          </div>
        )}

        {phase === "unlocked" && gift && (
          <div className="anim-in space-y-5">
            <p className="text-xs tracking-[0.35em]" style={{ color: theme.accent }}>
              {t("drop.unlocked")}
            </p>
            <p className="whitespace-pre-wrap text-2xl font-semibold leading-relaxed">
              {gift.message}
            </p>
            {gift.anonymous && gift.publicAnonId && (
              <p className="text-sm text-white/60">🕵️ {gift.publicAnonId}</p>
            )}
            <p className="text-xs anon-muted">
              {stepPick != null ? t("drop.yourPath") : ""}
            </p>
          </div>
        )}
      </div>

      {phase === "unlocked" && (
        <section className="mt-6 w-full space-y-3">
          <p className="font-semibold">{t("drop.yourTurn")}</p>
          <Link href="/drop" className="anon-btn anon-btn-primary w-full">
            🔥 {t("drop.sendBack")}
          </Link>
          <Link href="/moments" className="anon-btn anon-btn-ghost w-full">
            💜 {t("nav.moments")}
          </Link>
          <Link href="/games" className="anon-btn anon-btn-ghost w-full">
            🎮 {t("nav.games")}
          </Link>
        </section>
      )}
    </main>
  );
}
