"use client";

import { GAME_META } from "@/lib/games/definitions";
import type { GameModeDef } from "@/lib/games/catalog";
import { useI18n } from "@/components/I18nProvider";

const ART_CLASS: Record<string, string> = {
  mystery: "from-[#1a1228]/90 via-[#2d1b4a]/50 to-[#0e0a16]",
  roles: "from-[#2a1f45]/85 via-[#3d2a5c]/45 to-[#120e1c]",
  crowd: "from-[#1a2038]/80 via-[#2a2850]/45 to-[#0e101c]",
  grid: "from-[#2e1a2e]/85 via-[#4a2848]/45 to-[#120e1a]",
  liar: "from-[#241838]/80 via-[#3a2448]/45 to-[#100c1c]",
  speed: "from-[#32203a]/75 via-[#4a3050]/40 to-[#141018]",
  caption: "from-[#3a2448]/70 via-[#503060]/40 to-[#1a1224]",
  voice: "from-[#25204a]/80 via-[#2a2850]/45 to-[#0c0a18]",
  match: "from-[#2a2638]/80 via-[#3a3450]/40 to-[#121018]",
};

export function GameCard({
  mode,
  featured,
  onPlay,
  busy,
}: {
  mode: GameModeDef;
  featured?: boolean;
  onPlay: () => void;
  busy?: boolean;
}) {
  const { t } = useI18n();
  const meta = GAME_META[mode.id];
  const art = meta?.art || "mystery";
  const chaos = meta?.chaos || 3;

  return (
    <article
      className={`group relative overflow-hidden rounded-3xl border border-white/10 transition hover:-translate-y-0.5 hover:border-white/25 ${
        featured ? "sm:col-span-2" : ""
      }`}
    >
      <div
        className={`relative flex min-h-[200px] flex-col justify-end bg-gradient-to-br p-5 ${ART_CLASS[art]}`}
      >
        <div className="pointer-events-none absolute inset-0 opacity-40">
          <div className="absolute -right-6 -top-6 text-[7rem] leading-none opacity-30 transition group-hover:scale-105">
            {mode.emoji}
          </div>
          <div className="absolute bottom-0 left-0 h-1/2 w-full bg-gradient-to-t from-black/70 to-transparent" />
        </div>

        <div className="relative z-10">
          <p className="text-xs uppercase tracking-[0.2em] text-white/50">
            {t(meta?.categoryKey || "cat.mystery")}
          </p>
          <h3 className={`mt-1 font-semibold ${featured ? "text-2xl" : "text-xl"}`}>
            {mode.emoji} {t(mode.nameKey)}
          </h3>
          <p className="mt-2 max-w-md text-sm text-white/75">{t(mode.descKey)}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-white/60">
            <span>
              {t("game.players", { min: mode.minPlayers, max: mode.maxPlayers })}
            </span>
            <span>·</span>
            <span>{t("game.duration", { min: mode.durationMin })}</span>
            <span>·</span>
            <span aria-label={t("game.chaos", { n: chaos })}>
              {"⚡".repeat(chaos)}
            </span>
            {mode.free ? (
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-emerald-300">
                {t("game.free")}
              </span>
            ) : null}
            {!mode.playable ? (
              <span className="rounded-full bg-white/10 px-2 py-0.5">{t("game.coming")}</span>
            ) : null}
          </div>
          <button
            type="button"
            disabled={busy || !mode.playable}
            onClick={onPlay}
            className="anon-btn anon-btn-primary mt-4 w-full sm:w-auto disabled:opacity-40"
          >
            {mode.id === "random_5" ? t("game.playNow") : t("cta.playNow")}
          </button>
        </div>
      </div>
    </article>
  );
}
