"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { GAME_MODES, type GameModeDef } from "@/lib/games/catalog";
import { useI18n } from "@/components/I18nProvider";
import { GameCard } from "@/components/games/GameCard";

type Filter =
  | "all"
  | "friends"
  | "secret"
  | "funny"
  | "fast"
  | "strangers"
  | "teams";

export default function GamesPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const filters: { id: Filter; key: string }[] = [
    { id: "all", key: "games.filter.all" },
    { id: "friends", key: "games.filter.friends" },
    { id: "secret", key: "games.filter.secret" },
    { id: "funny", key: "games.filter.funny" },
    { id: "fast", key: "games.filter.fast" },
    { id: "strangers", key: "games.filter.strangers" },
    { id: "teams", key: "games.filter.teams" },
  ];

  const modes = useMemo(() => {
    return GAME_MODES.filter((m) => {
      if (filter === "all") return true;
      if (filter === "friends") return m.lanes.includes("friends");
      if (filter === "secret")
        return m.id === "secret_roles" || m.id === "find_the_liar" || m.id === "who_did_it";
      if (filter === "funny") return m.id === "caption_war" || m.id === "majority";
      if (filter === "fast") return m.durationMin <= 8 || m.id === "speed";
      if (filter === "strangers") return m.lanes.includes("anon") || m.lanes.includes("live");
      if (filter === "teams") return m.lanes.includes("battle");
      return true;
    });
  }, [filter]);

  const featured = modes.filter((m) => m.playable).slice(0, 2);
  const rest = modes.filter((m) => !featured.includes(m));

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
        <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">{t("games.title")}</h1>
        <p className="mx-auto mt-3 max-w-md text-sm anon-muted">{t("games.sub")}</p>
      </section>

      <section className="anon-card flex flex-col items-center gap-3 p-5 text-center sm:flex-row sm:justify-between sm:text-left">
        <div>
          <h2 className="text-lg font-semibold">{t("games.playNowTitle")}</h2>
          <p className="text-sm anon-muted">{t("games.playNowSub")}</p>
        </div>
        <button
          type="button"
          disabled={busy}
          className="anon-btn anon-btn-primary"
          onClick={() => {
            const m = GAME_MODES.find((x) => x.id === "random_5");
            if (m) create(m);
          }}
        >
          {t("cta.playNow")}
        </button>
      </section>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {filters.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => setFilter(f.id)}
            className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              filter === f.id
                ? "bg-violet-500/30 text-violet-100 ring-1 ring-violet-400/40"
                : "bg-white/5 anon-muted hover:bg-white/10"
            }`}
          >
            {t(f.key)}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] anon-muted">
          🔥 {t("home.popular")}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {featured.map((m) => (
            <GameCard
              key={m.id}
              mode={m}
              featured
              busy={busy}
              onPlay={() => create(m)}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] anon-muted">
          {t("games.all")}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {rest.map((m) => (
            <GameCard key={m.id} mode={m} busy={busy} onPlay={() => create(m)} />
          ))}
        </div>
      </section>

      <p className="text-center text-xs anon-muted">
        {t("home.freeNote")} · {GAME_MODES.filter((m) => m.playable).length}{" "}
        {t("games.playableCount")}
      </p>
    </main>
  );
}
