"use client";

import Link from "next/link";
import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { GAME_MODES, HOME_LANES, type GameModeDef } from "@/lib/games/catalog";
import { useI18n } from "@/components/I18nProvider";

function PlayInner() {
  const { t } = useI18n();
  const params = useSearchParams();
  const lane = params.get("lane");
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const modes = useMemo(() => {
    if (!lane || lane === "rank") return GAME_MODES;
    return GAME_MODES.filter((m) => m.lanes.includes(lane as never));
  }, [lane]);

  async function create(mode: GameModeDef) {
    setBusy(true);
    setError("");
    const r = await fetch("/api/games/rooms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        modeId: mode.id,
        randomMatch: mode.id === "random_5",
      }),
    });
    const d = await r.json();
    setBusy(false);
    if (!r.ok) {
      setError(d.error || t("error.generic"));
      return;
    }
    if (d.room?.myPlayerId) {
      localStorage.setItem(`anon_room_${d.room.code}`, d.room.myPlayerId);
    }
    router.push(`/r/${d.room.code}`);
  }

  return (
    <main className="anim-in space-y-6">
      <section className="text-center">
        <p className="text-xs tracking-[0.35em] text-violet-300">ANON</p>
        <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">{t("play.title")}</h1>
        <p className="mx-auto mt-3 max-w-md text-sm anon-muted">{t("play.sub")}</p>
        <p className="mt-2 text-xs anon-muted">{t("home.freeNote")}</p>
      </section>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {HOME_LANES.map((l) => (
          <Link
            key={l.id}
            href={l.href}
            className={`anon-card p-3 text-left transition hover:border-white/20 ${
              lane === l.id ? "ring-2 ring-violet-400/40" : ""
            }`}
          >
            <div className="text-xl">{l.emoji}</div>
            <div className="mt-1 text-xs font-bold">{t(l.titleKey)}</div>
            <div className="text-[11px] anon-muted">{t(l.descKey)}</div>
          </Link>
        ))}
      </div>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <section className="space-y-3">
        {modes.map((m) => (
          <div key={m.id} className="anon-card flex items-start gap-4 p-4">
            <span className="text-3xl">{m.emoji}</span>
            <div className="flex-1">
              <h2 className="font-semibold">{t(m.nameKey)}</h2>
              <p className="text-sm anon-muted">{t(m.descKey)}</p>
              <p className="mt-1 text-xs anon-muted">
                {t("game.players", { min: m.minPlayers, max: m.maxPlayers })} ·{" "}
                {t("game.duration", { min: m.durationMin })}
                {!m.playable ? ` · ${t("game.coming")}` : ""}
              </p>
            </div>
            <button
              type="button"
              disabled={busy || !m.playable}
              onClick={() => create(m)}
              className="anon-btn anon-btn-primary !px-3 !py-2 text-xs disabled:opacity-40"
            >
              {m.id === "random_5" ? t("game.playNow") : t("game.create")}
            </button>
          </div>
        ))}
      </section>

      <section className="anon-card p-5 text-center">
        <p className="font-medium">{t("play.after")}</p>
        <p className="mt-1 text-sm anon-muted">{t("play.after.desc")}</p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <Link href="/create" className="anon-btn anon-btn-ghost">
            💌 {t("product.moment")}
          </Link>
          <Link href="/anonymous" className="anon-btn anon-btn-ghost">
            🕵️ {t("product.anon")}
          </Link>
        </div>
      </section>
    </main>
  );
}

export default function PlayPage() {
  return (
    <Suspense>
      <PlayInner />
    </Suspense>
  );
}
