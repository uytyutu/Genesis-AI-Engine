"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/components/I18nProvider";

export default function RankPage() {
  const { t } = useI18n();
  const [top, setTop] = useState<
    { display_name: string; xp: number; league: string; wins: number; games: number }[]
  >([]);
  const [me, setMe] = useState<{ xp: number; league: string; wins: number; games: number } | null>(
    null
  );

  useEffect(() => {
    fetch("/api/games/rank")
      .then((r) => r.json())
      .then((d) => {
        setTop(d.top || []);
        setMe(d.me || null);
      });
  }, []);

  return (
    <main className="anim-in space-y-6">
      <h1 className="text-3xl font-semibold">🏆 {t("rank.title")}</h1>
      <p className="text-sm anon-muted">{t("rank.leagues")}</p>
      {me && (
        <div className="anon-card p-4">
          <p className="text-sm anon-muted">{t("rank.you")}</p>
          <p className="text-xl font-semibold capitalize">
            {me.league} · {me.xp} XP
          </p>
          <p className="text-sm anon-muted">
            {t("rank.winsGames", { wins: me.wins, games: me.games })}
          </p>
        </div>
      )}
      <div className="space-y-2">
        {top.length === 0 && (
          <div className="anon-card p-6 text-center text-sm anon-muted">
            {t("rank.empty")}{" "}
            <Link href="/play" className="underline">
              {t("rank.playSomething")}
            </Link>
          </div>
        )}
        {top.map((row, i) => (
          <div
            key={`${row.display_name}-${i}`}
            className="anon-card flex justify-between p-3 text-sm"
          >
            <span>
              #{i + 1} {row.display_name}
            </span>
            <span className="anon-muted capitalize">
              {row.league} · {row.xp}
            </span>
          </div>
        ))}
      </div>
    </main>
  );
}
