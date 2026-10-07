"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { getMode } from "@/lib/games/catalog";
import { majorityOptionsFor } from "@/lib/games/definitions";
import { useI18n } from "@/components/I18nProvider";
import { PhaseTimer } from "@/components/games/PhaseTimer";
import { RoleCard } from "@/components/games/RoleCard";
import { PaywallSheet } from "@/components/PaywallSheet";
import type { RoleId } from "@/lib/games/definitions";

type Player = {
  id: string;
  display_label: string;
  seat: number;
  score: number;
  ready?: boolean;
  isBot?: boolean;
  botDifficulty?: string | null;
  botStyleKey?: string | null;
};

type Room = {
  id: string;
  code: string;
  modeId: string;
  hostId: string | null;
  status: string;
  phase: string;
  maxPlayers: number;
  serverNow: string;
  phaseStartedAt: string | null;
  phaseEndsAt: string | null;
  state: Record<string, unknown>;
  botLimit?: number;
  botCount?: number;
  canHardBots?: boolean;
  players: Player[];
  myRole?: RoleId | null;
  myBriefKey?: string | null;
  myPlayerId?: string | null;
};

type ChatMsg = {
  id: string;
  body: string;
  created_at: string;
  player_id: string;
  display_label: string;
};

const REACTIONS = ["😂", "🔥", "👀", "😱", "👏", "🤔"];

export default function RoomPage() {
  const { t } = useI18n();
  const { code } = useParams<{ code: string }>();
  const [room, setRoom] = useState<Room | null>(null);
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [label, setLabel] = useState("");
  const [text, setText] = useState("");
  const [chatBody, setChatBody] = useState("");
  const [chat, setChat] = useState<ChatMsg[]>([]);
  const [reactions, setReactions] = useState<{ emoji: string }[]>([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [botDiff, setBotDiff] = useState<"easy" | "normal" | "hard">("normal");
  const [showBotPicker, setShowBotPicker] = useState(false);
  const [paywall, setPaywall] = useState<"bots" | "hard" | null>(null);

  function localizeLine(text: string) {
    if (text.startsWith("bot.") || text.startsWith("opt.") || text.startsWith("prompt.")) {
      return t(text);
    }
    return text;
  }

  const refresh = useCallback(async () => {
    const q = playerId ? `?playerId=${encodeURIComponent(playerId)}` : "";
    const r = await fetch(`/api/games/rooms/${code}${q}`);
    const d = await r.json();
    if (r.ok) {
      setRoom(d.room);
      if (d.chat) setChat(d.chat);
      if (d.reactions) setReactions(d.reactions);
    }
  }, [code, playerId]);

  useEffect(() => {
    const saved = localStorage.getItem(`anon_room_${code}`);
    if (saved) setPlayerId(saved);
  }, [code]);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 1500);
    return () => clearInterval(timer);
  }, [refresh]);

  const mode = useMemo(() => (room ? getMode(room.modeId) : null), [room]);
  const shareUrl =
    typeof window !== "undefined" ? `${window.location.origin}/r/${code}` : `/r/${code}`;

  async function post(body: Record<string, unknown>) {
    const r = await fetch(`/api/games/rooms/${code}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const d = await r.json();
    if (!r.ok) {
      const codeErr = String(d.error || "");
      if (codeErr === "FREE_BOT_LIMIT") {
        setError(t("bot.err.freeLimit"));
        setPaywall("bots");
      } else if (codeErr === "HARD_BOTS_LOCKED") {
        setError(t("bot.err.hardLocked"));
        setPaywall("hard");
      } else if (codeErr === "PREMIUM_BOT_LIMIT") setError(t("bot.err.premiumLimit"));
      else setError(codeErr || t("error.generic"));
      return { error: codeErr };
    }
    if (d.room) setRoom(d.room);
    if (d.chat) setChat(d.chat);
    if (d.reactions) setReactions(d.reactions);
    setError("");
    return d;
  }

  async function join() {
    const d = await post({
      action: "join",
      displayLabel: label || t("room.namePlaceholder"),
    });
    if (!d?.room) return;
    const me = d.room.myPlayerId || d.room.players[d.room.players.length - 1]?.id;
    if (me) {
      setPlayerId(me);
      localStorage.setItem(`anon_room_${code}`, me);
    }
  }

  async function play(type: string, payload: Record<string, unknown> = {}) {
    if (!playerId) {
      setError(t("cta.joinRoom"));
      return;
    }
    await post({ action: "play", playerId, type, payload });
    setText("");
  }

  const promptKey = String(room?.state.currentPromptKey || "");
  const lastReveal = room?.state.lastReveal as Record<string, unknown> | null;
  const answers = (room?.state.answers as Record<string, string>) || {};
  const votes = (room?.state.votes as Record<string, string>) || {};
  const submitted = Boolean(playerId && (votes[playerId] || answers[playerId]));
  const grid = (room?.state.grid as { i: number; opened: boolean; kind: string }[]) || [];
  const round = Number(room?.state.round || 0) + 1;
  const maxRounds = Number(room?.state.maxRounds || 3);

  if (!room) {
    return <main className="anim-pulse p-8 text-center">{t("room.finding")}</main>;
  }

  const ranked = [...room.players].sort((a, b) => b.score - a.score);
  const phaseLabel = t(`phase.${room.phase}`) || t("room.status.live");

  return (
    <main className="anim-in mx-auto grid max-w-5xl gap-4 lg:grid-cols-[200px_1fr_240px]">
      {/* Players — desktop left / mobile top */}
      <aside className="anon-card order-2 p-4 lg:order-1">
        <h2 className="text-xs font-semibold uppercase tracking-[0.2em] anon-muted">
          {t("room.players")}
        </h2>
        <ul className="mt-3 space-y-2 text-sm">
          {room.players.map((p) => (
            <li key={p.id} className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 truncate">
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${
                    p.isBot ? "bg-sky-400" : "bg-emerald-400"
                  }`}
                />
                <span className="truncate">
                  {p.isBot ? "🤖 " : ""}
                  {p.display_label}
                  {p.id === playerId ? ` ${t("room.you")}` : ""}
                </span>
              </span>
              <span className="shrink-0 tabular-nums anon-muted">{p.score}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs anon-muted">
          {room.players.length} / {room.maxPlayers}
        </p>
      </aside>

      {/* Center gameplay */}
      <section className="order-1 space-y-4 lg:order-2">
        <header className="anon-card flex flex-wrap items-start justify-between gap-3 p-4">
          <div>
            <p className="text-xs tracking-[0.25em] text-violet-300">
              {mode?.emoji} {mode ? t(mode.nameKey) : ""}
            </p>
            <h1 className="mt-1 text-xl font-semibold sm:text-2xl">{phaseLabel}</h1>
            {room.status === "live" && (
              <p className="mt-1 text-xs anon-muted">
                {t("room.round", { n: round, max: maxRounds })}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            {(room.status === "live" || room.phase === "role_reveal") && (
              <PhaseTimer phaseEndsAt={room.phaseEndsAt} serverNow={room.serverNow} />
            )}
            <button
              type="button"
              className="text-xs text-sky-300 underline"
              onClick={() => {
                navigator.clipboard.writeText(shareUrl);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? t("room.copied") : t("cta.copyLink")}
            </button>
          </div>
        </header>

        {/* Join */}
        {!playerId && room.status === "lobby" && (
          <section className="anon-card space-y-3 p-5">
            <input
              className="anon-input"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder={t("room.namePlaceholder")}
            />
            <button type="button" className="anon-btn anon-btn-primary w-full" onClick={join}>
              {t("cta.joinRoom")}
            </button>
          </section>
        )}

        {/* Lobby */}
        {room.status === "lobby" && playerId && (
          <section className="anon-card space-y-4 p-6">
            <div className="text-center">
              <p className="text-3xl">{mode?.emoji}</p>
              <h2 className="mt-2 text-2xl font-semibold">{mode ? t(mode.nameKey) : ""}</h2>
              <p className="mt-1 text-sm anon-muted">
                {mode
                  ? `${t("game.players", { min: mode.minPlayers, max: mode.maxPlayers })} · ${t("game.duration", { min: mode.durationMin })}`
                  : ""}
              </p>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] anon-muted">
                {t("room.players")}
              </p>
              {room.players.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between rounded-xl bg-black/20 px-3 py-2 text-sm"
                >
                  <span>
                    {p.isBot ? "🤖" : "👤"} {p.display_label}
                    {p.id === playerId ? ` ${t("room.you")}` : ""}
                    {p.isBot && p.botStyleKey ? (
                      <span className="ml-2 text-xs anon-muted">{t(p.botStyleKey)}</span>
                    ) : null}
                  </span>
                  {p.isBot ? (
                    <button
                      type="button"
                      className="text-xs text-rose-300"
                      onClick={() => post({ action: "remove_bot", botPlayerId: p.id })}
                    >
                      {t("bot.remove")}
                    </button>
                  ) : null}
                </div>
              ))}
              {Array.from({
                length: Math.max(0, Math.min(3, room.maxPlayers - room.players.length)),
              }).map((_, i) => (
                <div key={`slot${i}`} className="rounded-xl border border-dashed border-white/10 px-3 py-2 text-sm anon-muted">
                  🤖 {t("bot.slot")}
                </div>
              ))}
            </div>

            <p className="text-center text-sm anon-muted">
              {room.players.length} / {room.maxPlayers} · {t("bot.limit", {
                n: room.botCount || 0,
                max: room.botLimit || 2,
              })}
            </p>

            {!showBotPicker ? (
              <button
                type="button"
                className="anon-btn anon-btn-ghost w-full"
                onClick={() => setShowBotPicker(true)}
                disabled={room.players.length >= room.maxPlayers}
              >
                + {t("bot.add")}
              </button>
            ) : (
              <div className="space-y-2 rounded-2xl bg-black/25 p-3">
                <p className="text-xs anon-muted">{t("bot.pickDifficulty")}</p>
                {(
                  [
                    ["easy", "bot.diff.easy"],
                    ["normal", "bot.diff.normal"],
                    ["hard", "bot.diff.hard"],
                  ] as const
                ).map(([id, key]) => (
                  <button
                    key={id}
                    type="button"
                    className={`anon-btn w-full !justify-start ${
                      botDiff === id ? "anon-btn-primary" : "anon-btn-ghost"
                    } ${id === "hard" && !room.canHardBots ? "opacity-60" : ""}`}
                    onClick={() => setBotDiff(id)}
                  >
                    {id === "easy" ? "🟢" : id === "normal" ? "🟡" : "🔴"} {t(key)}
                    {id === "hard" && !room.canHardBots ? ` · ${t("bot.plusOnly")}` : ""}
                  </button>
                ))}
                <button
                  type="button"
                  className="anon-btn anon-btn-primary w-full"
                  onClick={async () => {
                    const d = await post({ action: "add_bot", difficulty: botDiff });
                    if (d && !("error" in d && d.error)) setShowBotPicker(false);
                  }}
                >
                  {t("bot.confirmAdd")}
                </button>
                <Link href="/plus" className="block text-center text-xs text-violet-300 underline">
                  {t("cta.viewPlus")}
                </Link>
              </div>
            )}

            <div className="flex flex-col gap-2 sm:flex-row">
              <button
                type="button"
                className="anon-btn anon-btn-ghost flex-1"
                onClick={() => post({ action: "ready", playerId, ready: true })}
              >
                {t("cta.ready")}
              </button>
              <button
                type="button"
                className="anon-btn anon-btn-primary flex-1"
                onClick={() => post({ action: "start" })}
                disabled={room.players.length < 2}
              >
                {t("cta.startGame")}
              </button>
            </div>
            {room.players.length < 2 && (
              <p className="text-center text-xs text-amber-200/90">{t("bot.needMore")}</p>
            )}
          </section>
        )}

        {/* Role reveal */}
        {room.phase === "role_reveal" && (
          <section className="anon-card space-y-4 p-6">
            <RoleCard role={room.myRole} />
            <p className="text-center text-sm anon-muted">{t("role.wait")}</p>
          </section>
        )}

        {/* Majority / random_5 question */}
        {room.status === "live" &&
          (room.modeId === "majority" || room.modeId === "random_5") &&
          room.phase === "question" && (
            <section className="anon-card space-y-4 p-5">
              <p className="text-xs uppercase tracking-[0.2em] anon-muted">{t("phase.question")}</p>
              <p className="text-xl font-semibold">{t(promptKey)}</p>
              <div className="grid gap-2">
                {majorityOptionsFor(promptKey).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    disabled={submitted}
                    className="anon-btn anon-btn-ghost w-full disabled:opacity-40"
                    onClick={() => play("pick_option", { choice: opt })}
                  >
                    {t(opt)}
                  </button>
                ))}
              </div>
              {submitted && <p className="text-sm text-emerald-300">{t("room.locked")}</p>}
            </section>
          )}

        {/* Who did it / secret roles — pick player */}
        {room.status === "live" &&
          (room.modeId === "who_did_it" || room.modeId === "secret_roles") &&
          (room.phase === "question" || room.phase === "vote") && (
            <section className="anon-card space-y-4 p-5">
              <p className="text-xs uppercase tracking-[0.2em] anon-muted">
                {room.phase === "vote" ? t("phase.vote") : t("phase.question")}
              </p>
              <p className="text-xl font-semibold">{t(promptKey)}</p>
              <div className="grid gap-2">
                {room.players
                  .filter((p) => p.id !== playerId)
                  .map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      disabled={submitted}
                      className="anon-btn anon-btn-ghost w-full disabled:opacity-40"
                      onClick={() => play("vote", { targetPlayerId: p.id })}
                    >
                      {p.display_label}
                    </button>
                  ))}
              </div>
              {submitted && <p className="text-sm text-emerald-300">{t("room.locked")}</p>}
            </section>
          )}

        {/* Find the liar */}
        {room.status === "live" && room.modeId === "find_the_liar" && room.phase === "answer" && (
          <section className="anon-card space-y-4 p-5">
            <p className="text-xs uppercase tracking-[0.2em] anon-muted">{t("phase.answer")}</p>
            <p className="text-lg font-semibold">
              {t(room.myBriefKey || "prompt.liar.brief.truth")}
            </p>
            <p className="text-sm anon-muted">{t("room.liarHint")}</p>
            <textarea
              className="anon-input min-h-24"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={submitted}
            />
            <button
              type="button"
              disabled={submitted || !text.trim()}
              className="anon-btn anon-btn-primary w-full disabled:opacity-40"
              onClick={() => play("answer", { text })}
            >
              {t("room.sendAnswer")}
            </button>
          </section>
        )}

        {room.status === "live" && room.modeId === "find_the_liar" && room.phase === "vote" && (
          <section className="anon-card space-y-4 p-5">
            <p className="text-xl font-semibold">{t("room.whoLiar")}</p>
            <div className="space-y-2 text-sm">
              {Object.entries(answers).map(([pid, ans]) => {
                const pl = room.players.find((p) => p.id === pid);
                return (
                  <div key={pid} className="rounded-xl bg-black/20 p-3">
                    <span className="anon-muted">{pl?.display_label}: </span>
                    {localizeLine(ans)}
                  </div>
                );
              })}
            </div>
            <div className="grid gap-2">
              {room.players
                .filter((p) => p.id !== playerId)
                .map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    disabled={submitted}
                    className="anon-btn anon-btn-ghost w-full disabled:opacity-40"
                    onClick={() => play("vote_liar", { targetPlayerId: p.id })}
                  >
                    🤥 {p.display_label}
                  </button>
                ))}
            </div>
          </section>
        )}

        {/* 5×5 grid */}
        {room.status === "live" && room.modeId === "battle_5x5" && room.phase === "action" && (
          <section className="anon-card space-y-4 p-5">
            <p className="text-lg font-semibold">{t("prompt.grid.pick")}</p>
            <div className="grid grid-cols-5 gap-1.5">
              {grid.map((cell) => (
                <div
                  key={cell.i}
                  className={`flex aspect-square items-center justify-center rounded-lg text-[10px] ${
                    cell.opened
                      ? "bg-violet-500/40 text-white"
                      : "bg-white/5 text-white/30"
                  } ${Number(room.state.cursor) === cell.i ? "ring-2 ring-sky-400" : ""}`}
                >
                  {cell.opened ? t(`grid.${cell.kind}`) : "·"}
                </div>
              ))}
            </div>
            <div className="grid gap-2">
              {room.players
                .filter((p) => p.id !== playerId)
                .map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    disabled={submitted}
                    className="anon-btn anon-btn-ghost w-full disabled:opacity-40"
                    onClick={() => play("vote", { targetPlayerId: p.id })}
                  >
                    {p.display_label}
                  </button>
                ))}
            </div>
          </section>
        )}

        {/* Caption war */}
        {room.status === "live" && room.modeId === "caption_war" && room.phase === "answer" && (
          <section className="anon-card space-y-4 p-5">
            <div className="flex h-32 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-900/50 to-violet-900/40 text-5xl">
              📸
            </div>
            <p className="text-lg font-semibold">{t(promptKey || "prompt.caption.five")}</p>
            <textarea
              className="anon-input min-h-20"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={submitted}
            />
            <button
              type="button"
              disabled={submitted || !text.trim()}
              className="anon-btn anon-btn-primary w-full disabled:opacity-40"
              onClick={() => play("caption", { text })}
            >
              {t("room.dropCaption")}
            </button>
          </section>
        )}

        {room.status === "live" && room.modeId === "caption_war" && room.phase === "vote" && (
          <section className="anon-card space-y-3 p-5">
            <p className="font-semibold">{t("phase.vote")}</p>
            {Object.entries(answers).map(([pid, caption]) =>
              pid === playerId ? null : (
                <button
                  key={pid}
                  type="button"
                  disabled={submitted}
                  className="anon-btn anon-btn-ghost w-full text-left disabled:opacity-40"
                  onClick={() => play("vote", { targetPlayerId: pid })}
                >
                  {localizeLine(caption)}
                </button>
              )
            )}
          </section>
        )}

        {/* Speed */}
        {room.status === "live" && room.modeId === "speed" && room.phase === "answer" && (
          <section className="anon-card space-y-4 p-5">
            <p className="text-xl font-semibold">{t(promptKey)}</p>
            <input
              className="anon-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={submitted}
            />
            <button
              type="button"
              disabled={submitted || !text.trim()}
              className="anon-btn anon-btn-primary w-full disabled:opacity-40"
              onClick={() => play("answer", { text })}
            >
              {t("room.lockIn")}
            </button>
          </section>
        )}

        {/* Reveal */}
        {room.phase === "reveal" && lastReveal && (
          <section className="anon-card space-y-4 p-6 text-center anim-in">
            <p className="text-xs uppercase tracking-[0.3em] text-violet-300">
              {t("phase.reveal")}
            </p>
            {lastReveal.type === "majority" && (
              <>
                <p className="text-3xl font-bold">{t(String(lastReveal.winner || ""))}</p>
                <p className="text-sm anon-muted">{t("room.majorityPicked")}</p>
              </>
            )}
            {lastReveal.type === "who" && (
              <>
                <p className="text-3xl font-bold">{String(lastReveal.targetLabel || "")}</p>
                <p className="text-sm anon-muted">{t("room.majorityThinks")}</p>
              </>
            )}
            {lastReveal.type === "liar" && (
              <>
                <p className="text-3xl font-bold">{String(lastReveal.liarLabel || "")}</p>
                <p className="text-sm anon-muted">
                  {lastReveal.caught ? t("room.liarCaught") : t("room.liarEscaped")}
                </p>
              </>
            )}
            {lastReveal.type === "grid" && (
              <p className="text-lg">
                {t("room.cellOpened", { kind: t(`grid.${String(lastReveal.kind)}`) })}
              </p>
            )}
            {lastReveal.type === "caption" && (
              <p className="text-lg">{t("room.captionWinner")}</p>
            )}
            <p className="text-emerald-300">+XP</p>
          </section>
        )}

        {/* Result */}
        {room.status === "finished" && (
          <section className="anon-card space-y-4 p-6 text-center">
            <p className="text-4xl">🏆</p>
            <h2 className="text-2xl font-semibold">{t("room.gameOver")}</h2>
            <ol className="space-y-2 text-left">
              {ranked.map((p, i) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between rounded-xl bg-black/20 px-3 py-2"
                >
                  <span>
                    {i === 0 ? "🏆" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}.`}{" "}
                    {p.display_label}
                  </span>
                  <span className="tabular-nums anon-muted">{p.score} XP</span>
                </li>
              ))}
            </ol>
            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
              <button
                type="button"
                className="anon-btn anon-btn-primary"
                onClick={() => playerId && post({ action: "rematch", playerId })}
              >
                {t("cta.rematch")}
              </button>
              <Link href="/games" className="anon-btn anon-btn-ghost">
                {t("cta.otherGame")}
              </Link>
              <button
                type="button"
                className="anon-btn anon-btn-ghost"
                onClick={() => {
                  const top = ranked[0]?.display_label || "";
                  navigator.clipboard.writeText(
                    t("share.result", { name: top, game: mode ? t(mode.nameKey) : "ANON" })
                  );
                }}
              >
                {t("cta.shareResult")}
              </button>
            </div>
            <div className="border-t border-white/10 pt-4">
              <p className="mb-2 text-sm anon-muted">{t("room.afterMoment")}</p>
              <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
                <Link href="/create" className="anon-btn anon-btn-ghost text-xs">
                  💌 {t("cta.sendMoment")}
                </Link>
                <Link href="/anonymous" className="anon-btn anon-btn-ghost text-xs">
                  🕵️ {t("cta.leaveAnon")}
                </Link>
              </div>
            </div>
          </section>
        )}

        {/* Reactions bar */}
        {playerId && room.status !== "finished" && (
          <div className="flex flex-wrap items-center justify-center gap-2">
            {REACTIONS.map((emoji) => (
              <button
                key={emoji}
                type="button"
                className="rounded-full bg-white/5 px-3 py-2 text-lg transition hover:bg-white/15"
                onClick={() => post({ action: "react", playerId, emoji })}
                aria-label={emoji}
              >
                {emoji}
              </button>
            ))}
          </div>
        )}
        {reactions.length > 0 && (
          <div className="flex justify-center gap-1 text-2xl">
            {reactions.slice(0, 6).map((r, i) => (
              <span key={i} className="anim-in">
                {r.emoji}
              </span>
            ))}
          </div>
        )}

        {error && <p className="text-sm text-rose-300">{error}</p>}

        <PaywallSheet
          open={paywall != null}
          onClose={() => setPaywall(null)}
          titleKey={paywall === "hard" ? "paywall.hardTitle" : "paywall.botsTitle"}
          bodyKey={paywall === "hard" ? "paywall.hardBody" : "paywall.botsBody"}
        />

        {/* Mobile chat toggle */}
        <button
          type="button"
          className="anon-btn anon-btn-ghost w-full lg:hidden"
          onClick={() => setChatOpen((v) => !v)}
        >
          💬 {t("room.chat")}
        </button>
        {chatOpen && (
          <ChatPanel
            chat={chat}
            chatBody={chatBody}
            setChatBody={setChatBody}
            onSend={() => {
              if (!playerId || !chatBody.trim()) return;
              post({ action: "chat", playerId, body: chatBody }).then(() => setChatBody(""));
            }}
            t={t}
            className="lg:hidden"
          />
        )}
      </section>

      {/* Desktop chat */}
      <aside className="order-3 hidden lg:block">
        <ChatPanel
          chat={chat}
          chatBody={chatBody}
          setChatBody={setChatBody}
          onSend={() => {
            if (!playerId || !chatBody.trim()) return;
            post({ action: "chat", playerId, body: chatBody }).then(() => setChatBody(""));
          }}
          t={t}
        />
      </aside>
    </main>
  );
}

function ChatPanel({
  chat,
  chatBody,
  setChatBody,
  onSend,
  t,
  className = "",
}: {
  chat: ChatMsg[];
  chatBody: string;
  setChatBody: (v: string) => void;
  onSend: () => void;
  t: (k: string, v?: Record<string, string | number>) => string;
  className?: string;
}) {
  return (
    <div className={`anon-card flex h-[420px] flex-col p-3 ${className}`}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] anon-muted">
        {t("room.chat")}
      </p>
      <div className="flex-1 space-y-2 overflow-y-auto text-sm">
        {chat.length === 0 && <p className="anon-muted">{t("room.chatEmpty")}</p>}
        {chat.map((m) => (
          <div key={m.id}>
            <span className="text-violet-300">{m.display_label}: </span>
            {m.body}
          </div>
        ))}
      </div>
      <div className="mt-2 flex gap-2">
        <input
          className="anon-input !py-2 text-xs"
          value={chatBody}
          onChange={(e) => setChatBody(e.target.value)}
          placeholder={t("room.chatPlaceholder")}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSend();
          }}
        />
        <button type="button" className="anon-btn anon-btn-primary !px-3 !py-2 text-xs" onClick={onSend}>
          {t("cta.send")}
        </button>
      </div>
    </div>
  );
}
