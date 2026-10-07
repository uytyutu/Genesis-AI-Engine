import crypto from "crypto";
import { getDb, type AnonDb } from "@/lib/db";
import {
  botLimitForUser,
  canUseHardBots,
  FREE_BOT_LIMIT,
  PREMIUM_BOT_LIMIT,
} from "@/lib/entitlements";
import { getMode, type GameModeId } from "./catalog";
import {
  decideBotAction,
  pickPersona,
  type BotDifficulty,
} from "./bots";
import {
  GAME_META,
  ROLES,
  type GamePhase,
  type RoleId,
} from "./definitions";

export type PublicRoom = {
  id: string;
  code: string;
  modeId: string;
  hostId: string | null;
  status: string;
  phase: GamePhase;
  maxPlayers: number;
  serverNow: string;
  phaseStartedAt: string | null;
  phaseEndsAt: string | null;
  state: Record<string, unknown>;
  createdAt: string;
  botLimit: number;
  botCount: number;
  canHardBots: boolean;
  players: {
    id: string;
    user_id: string | null;
    display_label: string;
    seat: number;
    score: number;
    ready: boolean;
    connected: boolean;
    isBot: boolean;
    botDifficulty?: BotDifficulty | null;
    botStyleKey?: string | null;
  }[];
  myRole?: RoleId | null;
  myBriefKey?: string | null;
  myPlayerId?: string | null;
};

function roomCode(): string {
  return crypto.randomBytes(3).toString("hex").toUpperCase();
}

function nowIso() {
  return new Date().toISOString();
}

async function ensureChatTables(db: AnonDb) {
  await db.exec(`
    CREATE TABLE IF NOT EXISTS game_chat (
      id TEXT PRIMARY KEY,
      room_id TEXT NOT NULL,
      player_id TEXT,
      body TEXT NOT NULL,
      kind TEXT NOT NULL DEFAULT 'text',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS game_reactions (
      id TEXT PRIMARY KEY,
      room_id TEXT NOT NULL,
      player_id TEXT,
      emoji TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
  `);
  for (const sql of [
    `ALTER TABLE game_players ADD COLUMN ready INTEGER NOT NULL DEFAULT 0`,
    `ALTER TABLE game_players ADD COLUMN is_bot INTEGER NOT NULL DEFAULT 0`,
    `ALTER TABLE game_players ADD COLUMN bot_difficulty TEXT`,
    `ALTER TABLE game_players ADD COLUMN bot_persona TEXT`,
  ]) {
    try {
      await db.exec(sql);
    } catch {
      /* exists */
    }
  }
}

export async function createRoom(input: {
  modeId: GameModeId;
  hostId?: string | null;
  hostLabel: string;
  maxPlayers?: number;
}) {
  const mode = getMode(input.modeId);
  if (!mode) throw new Error("Unknown mode");
  if (!mode.playable) throw new Error("Mode not playable yet");
  const db = await getDb();
  await ensureChatTables(db);
  const id = crypto.randomUUID();
  const code = roomCode();
  const now = nowIso();
  const max = input.maxPlayers || mode.maxPlayers;
  const state = buildInitialState(input.modeId);

  await db.prepare(
    `INSERT INTO game_rooms (id, code, mode_id, host_id, status, phase, max_players, state_json, created_at, updated_at)
     VALUES (?, ?, ?, ?, 'lobby', 'lobby', ?, ?, ?, ?)`
  ).run(id, code, input.modeId, input.hostId || null, max, JSON.stringify(state), now, now);

  const playerId = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO game_players (id, room_id, user_id, display_label, seat, score, joined_at, ready)
     VALUES (?, ?, ?, ?, 0, 0, ?, 0)`
  ).run(playerId, id, input.hostId || null, input.hostLabel, now);

  return getRoomPublic(code, playerId);
}

function buildInitialState(modeId: GameModeId): Record<string, unknown> {
  const meta = GAME_META[modeId];
  const base = {
    round: 0,
    maxRounds: meta.maxRounds,
    promptKeys: meta.promptKeys,
    phaseStartedAt: null as string | null,
    phaseEndsAt: null as string | null,
    votes: {} as Record<string, string>,
    answers: {} as Record<string, string>,
    results: [] as unknown[],
    roles: {} as Record<string, RoleId>,
    lastReveal: null as unknown,
  };

  if (modeId === "battle_5x5") {
    return {
      ...base,
      grid: Array.from({ length: 25 }, (_, i) => ({
        i,
        opened: false,
        kind: ["question", "bonus", "vote", "trap", "double"][i % 5],
      })),
      cursor: 0,
    };
  }
  if (modeId === "find_the_liar") {
    return { ...base, liarSeat: null, storyKey: "prompt.liar.story" };
  }
  if (modeId === "random_5") {
    return { ...base, promptKeys: GAME_META.majority.promptKeys };
  }
  return base;
}

async function loadRoomRow(code: string) {
  const db = await getDb();
  return (await db
    .prepare("SELECT * FROM game_rooms WHERE code = ?")
    .get(code.toUpperCase())) as
    | {
        id: string;
        code: string;
        mode_id: string;
        host_id: string | null;
        status: string;
        phase: string;
        max_players: number;
        state_json: string;
        created_at: string;
        updated_at: string;
      }
    | undefined;
}

async function saveRoom(
  roomId: string,
  patch: {
    state?: Record<string, unknown>;
    phase?: GamePhase;
    status?: string;
  }
) {
  const db = await getDb();
  const row = (await db
    .prepare("SELECT state_json, phase, status FROM game_rooms WHERE id = ?")
    .get(roomId)) as {
    state_json: string;
    phase: string;
    status: string;
  };
  const state = patch.state ?? JSON.parse(row.state_json || "{}");
  await db.prepare(
    `UPDATE game_rooms SET state_json = ?, phase = ?, status = ?, updated_at = ? WHERE id = ?`
  ).run(
    JSON.stringify(state),
    patch.phase ?? row.phase,
    patch.status ?? row.status,
    nowIso(),
    roomId
  );
}

function setPhaseTimer(state: Record<string, unknown>, seconds: number) {
  const start = Date.now();
  state.phaseStartedAt = new Date(start).toISOString();
  state.phaseEndsAt = new Date(start + seconds * 1000).toISOString();
}

async function playersOf(roomId: string) {
  const db = await getDb();
  return (await db
    .prepare(
      `SELECT id, user_id, display_label, seat, score, COALESCE(ready,0) as ready,
              COALESCE(is_bot,0) as is_bot, bot_difficulty, bot_persona
       FROM game_players WHERE room_id = ? ORDER BY seat ASC`
    )
    .all(roomId)) as {
    id: string;
    user_id: string | null;
    display_label: string;
    seat: number;
    score: number;
    ready: number;
    is_bot: number;
    bot_difficulty: string | null;
    bot_persona: string | null;
  }[];
}

export async function getRoomPublic(
  code: string,
  viewerPlayerId?: string | null
): Promise<PublicRoom | null> {
  await ensureChatTables(await getDb());
  const row = await loadRoomRow(code);
  if (!row) return null;
  await advanceIfTimedOut(row.code);
  const fresh = (await loadRoomRow(code))!;
  const state = JSON.parse(fresh.state_json || "{}") as Record<string, unknown>;
  const rawPlayers = await playersOf(fresh.id);
  const players = rawPlayers.map((p) => ({
    id: p.id,
    user_id: p.user_id,
    display_label: p.display_label,
    seat: p.seat,
    score: p.score,
    ready: Boolean(p.ready),
    connected: true,
    isBot: Boolean(p.is_bot),
    botDifficulty: (p.bot_difficulty as BotDifficulty) || null,
    botStyleKey: p.bot_persona
      ? `bot.style.${
          (
            {
              alex: "risky",
              mia: "majority",
              leo: "aggressive",
              nina: "bluff",
              sam: "careful",
              rio: "risky",
              kai: "majority",
              zoe: "bluff",
            } as Record<string, string>
          )[p.bot_persona] || "careful"
        }`
      : null,
  }));

  const publicState = { ...state };
  delete publicState.roles;
  if (fresh.mode_id === "find_the_liar") {
    delete publicState.liarSeat;
  }

  let myRole: RoleId | null = null;
  let myBriefKey: string | null = null;
  if (viewerPlayerId && state.roles && typeof state.roles === "object") {
    const roles = state.roles as Record<string, RoleId>;
    myRole = roles[viewerPlayerId] || null;
  }
  if (viewerPlayerId && fresh.mode_id === "find_the_liar" && fresh.status === "live") {
    const me = rawPlayers.find((p) => p.id === viewerPlayerId);
    const liarSeat = Number(state.liarSeat);
    const isLiar = me != null && me.seat === liarSeat;
    myBriefKey = isLiar ? "prompt.liar.brief.liar" : "prompt.liar.brief.truth";
  }

  const botCount = rawPlayers.filter((p) => p.is_bot).length;

  return {
    id: fresh.id,
    code: fresh.code,
    modeId: fresh.mode_id,
    hostId: fresh.host_id,
    status: fresh.status,
    phase: fresh.phase as GamePhase,
    maxPlayers: fresh.max_players,
    serverNow: nowIso(),
    phaseStartedAt: (state.phaseStartedAt as string) || null,
    phaseEndsAt: (state.phaseEndsAt as string) || null,
    state: publicState,
    createdAt: fresh.created_at,
    botLimit: await botLimitForUser(fresh.host_id),
    botCount,
    canHardBots: await canUseHardBots(fresh.host_id),
    players,
    myRole,
    myBriefKey,
    myPlayerId: viewerPlayerId || null,
  };
}

export async function getRoomByCode(code: string) {
  return getRoomPublic(code);
}

export async function joinRoom(code: string, label: string, userId?: string | null) {
  const row = await loadRoomRow(code);
  if (!row) throw new Error("Room not found");
  if (row.status !== "lobby") throw new Error("Game already started");
  const players = await playersOf(row.id);
  if (players.length >= row.max_players) throw new Error("Room full");

  const db = await getDb();
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO game_players (id, room_id, user_id, display_label, seat, score, joined_at, ready)
     VALUES (?, ?, ?, ?, ?, 0, ?, 0)`
  ).run(id, row.id, userId || null, label, players.length, nowIso());
  return getRoomPublic(code, id);
}

export async function setReady(code: string, playerId: string, ready: boolean) {
  const row = await loadRoomRow(code);
  if (!row || row.status !== "lobby") throw new Error("Not in lobby");
  const db = await getDb();
  await db
    .prepare(`UPDATE game_players SET ready = ? WHERE id = ? AND room_id = ?`)
    .run(ready ? 1 : 0, playerId, row.id);
  return getRoomPublic(code, playerId);
}

export async function addBot(
  code: string,
  difficulty: BotDifficulty = "normal",
  requesterUserId?: string | null
) {
  const row = await loadRoomRow(code);
  if (!row) throw new Error("Room not found");
  if (row.status !== "lobby") throw new Error("Game already started");
  const players = await playersOf(row.id);
  if (players.length >= row.max_players) throw new Error("Room full");

  const hostId = row.host_id;
  const limit = await botLimitForUser(hostId || requesterUserId);
  const bots = players.filter((p) => p.is_bot);
  if (bots.length >= limit) {
    const err = new Error(
      limit <= FREE_BOT_LIMIT ? "BOT_LIMIT_FREE" : "BOT_LIMIT_PREMIUM"
    );
    throw err;
  }

  let diff = difficulty;
  if (diff === "hard" && !(await canUseHardBots(hostId || requesterUserId))) {
    throw new Error("HARD_BOTS_LOCKED");
  }

  const used = new Set(players.map((p) => p.display_label));
  const persona = pickPersona(used);
  const id = crypto.randomUUID();
  const db = await getDb();
  await db
    .prepare(
      `INSERT INTO game_players
       (id, room_id, user_id, display_label, seat, score, joined_at, ready, is_bot, bot_difficulty, bot_persona)
       VALUES (?, ?, NULL, ?, ?, 0, ?, 1, 1, ?, ?)`
    )
    .run(id, row.id, persona.name, players.length, nowIso(), diff, persona.id);

  return getRoomPublic(code);
}

export async function removeBot(code: string, botPlayerId: string) {
  const row = await loadRoomRow(code);
  if (!row || row.status !== "lobby") throw new Error("Not in lobby");
  const db = await getDb();
  const bot = await db
    .prepare(
      `SELECT id FROM game_players WHERE id = ? AND room_id = ? AND COALESCE(is_bot,0) = 1`
    )
    .get(botPlayerId, row.id);
  if (!bot) throw new Error("Bot not found");
  await db.prepare(`DELETE FROM game_players WHERE id = ?`).run(botPlayerId);
  const left = await playersOf(row.id);
  for (let i = 0; i < left.length; i++) {
    await db.prepare(`UPDATE game_players SET seat = ? WHERE id = ?`).run(i, left[i].id);
  }
  return getRoomPublic(code);
}

async function runBotTurns(code: string) {
  const row = await loadRoomRow(code);
  if (!row || row.status !== "live") return;
  const phase = row.phase as GamePhase;
  if (phase === "reveal" || phase === "result" || phase === "role_reveal") return;

  const state = JSON.parse(row.state_json || "{}") as Record<string, unknown>;
  const votes = (state.votes as Record<string, string>) || {};
  const answers = (state.answers as Record<string, string>) || {};
  const players = await playersOf(row.id);
  const publicPlayers = players.map((p) => ({
    id: p.id,
    display_label: p.display_label,
    score: p.score,
    is_bot: Boolean(p.is_bot),
  }));

  for (const bot of players.filter((p) => p.is_bot)) {
    const already = Boolean(votes[bot.id]) || Boolean(answers[bot.id]);
    if (already) continue;

    const action = decideBotAction({
      modeId: row.mode_id as GameModeId,
      phase,
      botId: bot.id,
      personaId: bot.bot_persona || "alex",
      difficulty: (bot.bot_difficulty as BotDifficulty) || "normal",
      promptKey: String(state.currentPromptKey || ""),
      players: publicPlayers,
      votes,
      answers,
      round: Number(state.round || 0),
    });
    if (!action) continue;
    try {
      await applyAction(code, bot.id, action, { fromBot: true });
    } catch {
      /* already acted / phase moved */
    }
    const check = await loadRoomRow(code);
    if (!check || check.status !== "live" || check.phase !== phase) break;
  }
}

export async function startRoom(code: string, userId?: string | null) {
  const row = await loadRoomRow(code);
  if (!row) throw new Error("Room not found");
  if (row.host_id && userId && row.host_id !== userId) {
    throw new Error("Only host can start");
  }
  const mode = getMode(row.mode_id);
  if (!mode) throw new Error("Unknown mode");
  const players = await playersOf(row.id);
  const minP = Math.min(mode.minPlayers, 2);
  if (players.length < minP) throw new Error(`Need at least ${minP} players`);

  const state = JSON.parse(row.state_json || "{}") as Record<string, unknown>;

  if (row.mode_id === "secret_roles") {
    const roles: Record<string, RoleId> = {};
    players.forEach((p, i) => {
      roles[p.id] = ROLES[i % ROLES.length];
    });
    state.roles = roles;
    setPhaseTimer(state, 12);
    await saveRoom(row.id, { state, phase: "role_reveal", status: "live" });
    return getRoomPublic(code);
  }

  if (row.mode_id === "find_the_liar") {
    state.liarSeat = Math.floor(Math.random() * players.length);
  }

  state.round = 0;
  await beginQuestionPhase(row.id, row.mode_id as GameModeId, state);
  await runBotTurns(code);
  return getRoomPublic(code);
}

async function beginQuestionPhase(
  roomId: string,
  modeId: GameModeId,
  state: Record<string, unknown>
) {
  const meta = GAME_META[modeId];
  const round = Number(state.round || 0);
  const keys = (state.promptKeys as string[]) || meta.promptKeys;
  state.currentPromptKey = keys[round % Math.max(keys.length, 1)] || keys[0];
  state.votes = {};
  state.answers = {};
  state.lastReveal = null;

  let phase: GamePhase = "question";
  if (modeId === "find_the_liar" || modeId === "caption_war") phase = "answer";
  if (modeId === "battle_5x5") phase = "action";
  if (modeId === "speed") phase = "answer";

  setPhaseTimer(state, meta.roundSeconds);
  await saveRoom(roomId, { state, phase, status: "live" });
}

async function advanceIfTimedOut(code: string) {
  const row = await loadRoomRow(code);
  if (!row || row.status !== "live") return;
  const state = JSON.parse(row.state_json || "{}") as Record<string, unknown>;
  const ends = state.phaseEndsAt ? Date.parse(String(state.phaseEndsAt)) : 0;
  if (!ends || Date.now() < ends) return;

  const phase = row.phase as GamePhase;
  if (phase === "role_reveal") {
    state.round = 0;
    await beginQuestionPhase(row.id, row.mode_id as GameModeId, state);
    return;
  }
  if (phase === "question" || phase === "answer" || phase === "vote" || phase === "action") {
    await resolveRound(row.id, row.mode_id as GameModeId, state, phase);
  }
}

async function addScore(playerId: string, delta: number) {
  const db = await getDb();
  await db.prepare("UPDATE game_players SET score = score + ? WHERE id = ?").run(delta, playerId);
}

async function resolveRound(
  roomId: string,
  modeId: GameModeId,
  state: Record<string, unknown>,
  fromPhase: GamePhase
) {
  const players = await playersOf(roomId);
  const votes = (state.votes as Record<string, string>) || {};
  const answers = (state.answers as Record<string, string>) || {};
  const meta = GAME_META[modeId];

  if (modeId === "majority" || modeId === "random_5") {
    const counts: Record<string, number> = {};
    for (const v of Object.values(votes)) counts[v] = (counts[v] || 0) + 1;
    const winner = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];
    for (const p of players) {
      if (votes[p.id] === winner) await addScore(p.id, 120);
    }
    state.lastReveal = { type: "majority", winner, counts, votes };
  } else if (modeId === "who_did_it" || modeId === "secret_roles") {
    const counts: Record<string, number> = {};
    for (const v of Object.values(votes)) counts[v] = (counts[v] || 0) + 1;
    const target = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];
    for (const p of players) {
      if (votes[p.id] === target) await addScore(p.id, 100);
    }
    const targetLabel = players.find((p) => p.id === target)?.display_label;
    state.lastReveal = { type: "who", target, targetLabel, counts };
  } else if (modeId === "find_the_liar") {
    if (fromPhase === "answer") {
      setPhaseTimer(state, 20);
      await saveRoom(roomId, { state, phase: "vote", status: "live" });
      return;
    }
    const liar = players.find((p) => p.seat === Number(state.liarSeat));
    let caught = 0;
    for (const v of Object.values(votes)) {
      if (v === liar?.id) caught++;
    }
    if (caught > players.length / 2) {
      for (const p of players) {
        if (votes[p.id] === liar?.id) await addScore(p.id, 150);
      }
    } else if (liar) {
      await addScore(liar.id, 200);
    }
    state.lastReveal = {
      type: "liar",
      liarId: liar?.id,
      liarLabel: liar?.display_label,
      caught: caught > players.length / 2,
    };
  } else if (modeId === "battle_5x5") {
    const cursor = Number(state.cursor || 0);
    const grid = (state.grid as { i: number; opened: boolean; kind: string }[]) || [];
    if (grid[cursor]) grid[cursor].opened = true;
    state.grid = grid;
    state.cursor = cursor + 1;
    for (const p of players) {
      if (votes[p.id]) await addScore(p.id, 80);
    }
    state.lastReveal = { type: "grid", cell: cursor, kind: grid[cursor]?.kind };
  } else if (modeId === "caption_war") {
    if (fromPhase === "answer") {
      setPhaseTimer(state, 20);
      await saveRoom(roomId, { state, phase: "vote", status: "live" });
      return;
    }
    const counts: Record<string, number> = {};
    for (const v of Object.values(votes)) counts[v] = (counts[v] || 0) + 1;
    const win = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];
    if (win) await addScore(win, 180);
    state.lastReveal = { type: "caption", winnerId: win, answers, votes };
  } else if (modeId === "speed") {
    for (const p of players) {
      if (answers[p.id]) await addScore(p.id, 90);
    }
    state.lastReveal = { type: "speed", answers };
  }

  setPhaseTimer(state, 6);
  await saveRoom(roomId, { state, phase: "reveal", status: "live" });
  state._revealUntil = Date.now() + 6000;
}

async function maybeAfterReveal(code: string) {
  const row = await loadRoomRow(code);
  if (!row || row.phase !== "reveal") return;
  const state = JSON.parse(row.state_json || "{}") as Record<string, unknown>;
  const until = Number(state._revealUntil || 0);
  const ends = state.phaseEndsAt ? Date.parse(String(state.phaseEndsAt)) : 0;
  if (Date.now() < Math.max(until, ends)) return;

  const round = Number(state.round || 0) + 1;
  const meta = GAME_META[row.mode_id as GameModeId];
  state.round = round;
  if (round >= meta.maxRounds) {
    await finishGame(row.id, state);
    return;
  }
  await beginQuestionPhase(row.id, row.mode_id as GameModeId, state);
}

async function finishGame(roomId: string, state: Record<string, unknown>) {
  state.phaseEndsAt = null;
  await saveRoom(roomId, { state, phase: "result", status: "finished" });
  const db = await getDb();
  const codeRow = (await db
    .prepare("SELECT code FROM game_rooms WHERE id = ?")
    .get(roomId)) as { code: string };
  await awardXp(codeRow.code);
}

async function awardXp(code: string) {
  const room = await getRoomPublic(code);
  if (!room) return;
  const db = await getDb();
  const now = nowIso();
  const ranked = [...room.players].sort((a, b) => b.score - a.score);
  for (let i = 0; i < ranked.length; i++) {
    const p = ranked[i];
    if (!p.user_id) continue;
    const bonus = i === 0 ? 80 : i === 1 ? 40 : 20;
    const row = (await db
      .prepare("SELECT xp, wins, games FROM user_ranks WHERE user_id = ?")
      .get(p.user_id)) as { xp: number; wins: number; games: number } | undefined;
    const xp = (row?.xp || 0) + 40 + Math.floor(p.score / 10) + bonus;
    const wins = (row?.wins || 0) + (i === 0 ? 1 : 0);
    const games = (row?.games || 0) + 1;
    const league =
      xp >= 5000
        ? "legend"
        : xp >= 2500
          ? "diamond"
          : xp >= 1200
            ? "platinum"
            : xp >= 600
              ? "gold"
              : xp >= 250
                ? "silver"
                : "bronze";
    await db.prepare(
      `INSERT INTO user_ranks (user_id, xp, league, wins, games, updated_at)
       VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(user_id) DO UPDATE SET
         xp=excluded.xp, league=excluded.league, wins=excluded.wins,
         games=excluded.games, updated_at=excluded.updated_at`
    ).run(p.user_id, xp, league, wins, games, now);
  }
}

export async function applyAction(
  code: string,
  playerId: string,
  action: { type: string; payload?: Record<string, unknown> },
  opts?: { fromBot?: boolean }
) {
  await advanceIfTimedOut(code);
  await maybeAfterReveal(code);
  const row = await loadRoomRow(code);
  if (!row) throw new Error("Room not found");
  const players = await playersOf(row.id);
  const player = players.find((p) => p.id === playerId);
  if (!player) throw new Error("Not in room");

  if (action.type === "ready") {
    return setReady(code, playerId, Boolean(action.payload?.ready ?? true));
  }

  if (row.status !== "live") throw new Error("Game not live");
  const state = JSON.parse(row.state_json || "{}") as Record<string, unknown>;
  const phase = row.phase as GamePhase;
  const ends = state.phaseEndsAt ? Date.parse(String(state.phaseEndsAt)) : Infinity;
  if (Date.now() > ends && phase !== "reveal") {
    await advanceIfTimedOut(code);
    return getRoomPublic(code, playerId);
  }

  if (action.type === "vote" || action.type === "guess" || action.type === "vote_liar") {
    if (phase !== "question" && phase !== "vote" && phase !== "action") {
      throw new Error("Not voting phase");
    }
    const votes = { ...((state.votes as Record<string, string>) || {}) };
    if (votes[playerId]) throw new Error("Already voted");
    votes[playerId] = String(action.payload?.targetPlayerId || action.payload?.choice || "");
    state.votes = votes;
    await saveRoom(row.id, { state });
    if (Object.keys(votes).length >= players.length) {
      await resolveRound(
        row.id,
        row.mode_id as GameModeId,
        state,
        phase === "vote" ? "vote" : phase === "action" ? "action" : "question"
      );
    } else if (!opts?.fromBot) {
      await runBotTurns(code);
    }
    return getRoomPublic(code, playerId);
  }

  if (action.type === "answer" || action.type === "caption" || action.type === "submit_fact") {
    if (phase !== "answer" && phase !== "question") throw new Error("Not answer phase");
    const answers = { ...((state.answers as Record<string, string>) || {}) };
    if (answers[playerId]) throw new Error("Already answered");
    answers[playerId] = String(action.payload?.text || "").slice(0, 280);
    state.answers = answers;
    if (row.mode_id === "who_did_it" && Object.keys(answers).length >= players.length) {
      state.votes = {};
      setPhaseTimer(state, 20);
      await saveRoom(row.id, { state, phase: "vote", status: "live" });
      if (!opts?.fromBot) await runBotTurns(code);
      return getRoomPublic(code, playerId);
    }
    await saveRoom(row.id, { state });
    if (Object.keys(answers).length >= players.length) {
      await resolveRound(row.id, row.mode_id as GameModeId, state, "answer");
    } else if (!opts?.fromBot) {
      await runBotTurns(code);
    }
    return getRoomPublic(code, playerId);
  }

  if (action.type === "pick_option") {
    if (phase !== "question") throw new Error("Not question phase");
    const votes = { ...((state.votes as Record<string, string>) || {}) };
    if (votes[playerId]) throw new Error("Already answered");
    votes[playerId] = String(action.payload?.choice || "");
    state.votes = votes;
    await saveRoom(row.id, { state });
    if (Object.keys(votes).length >= players.length) {
      await resolveRound(row.id, row.mode_id as GameModeId, state, "question");
    } else if (!opts?.fromBot) {
      await runBotTurns(code);
    }
    return getRoomPublic(code, playerId);
  }

  throw new Error("Unsupported action");
}

export async function rematch(code: string, hostPlayerId: string) {
  const row = await loadRoomRow(code);
  if (!row || row.status !== "finished") throw new Error("No finished game");
  const players = await playersOf(row.id);
  if (!players.find((p) => p.id === hostPlayerId)) throw new Error("Not in room");

  const state = buildInitialState(row.mode_id as GameModeId);
  const db = await getDb();
  await db.prepare(`UPDATE game_players SET score = 0, ready = 0 WHERE room_id = ?`).run(row.id);
  await saveRoom(row.id, { state, phase: "lobby", status: "lobby" });
  return getRoomPublic(code, hostPlayerId);
}

export async function findOrCreateRandom5(label: string, userId?: string | null) {
  const db = await getDb();
  await ensureChatTables(db);
  const open = (await db
    .prepare(
      `SELECT code FROM game_rooms WHERE mode_id = 'random_5' AND status = 'lobby' ORDER BY created_at ASC LIMIT 1`
    )
    .get()) as { code: string } | undefined;
  if (open) {
    const room = await joinRoom(open.code, label, userId);
    if (room && room.players.length >= 5) {
      return startRoom(open.code, room.hostId);
    }
    return room;
  }
  return createRoom({ modeId: "random_5", hostId: userId, hostLabel: label, maxPlayers: 5 });
}

export async function postChat(code: string, playerId: string, body: string) {
  const row = await loadRoomRow(code);
  if (!row) throw new Error("Room not found");
  const players = await playersOf(row.id);
  if (!players.find((p) => p.id === playerId)) throw new Error("Not in room");
  const id = crypto.randomUUID();
  const db = await getDb();
  await db
    .prepare(
      `INSERT INTO game_chat (id, room_id, player_id, body, kind, created_at) VALUES (?, ?, ?, ?, 'text', ?)`
    )
    .run(id, row.id, playerId, body.slice(0, 240), nowIso());
  return { id };
}

export async function listChat(code: string) {
  const row = await loadRoomRow(code);
  if (!row) return [];
  const db = await getDb();
  const rows = await db
    .prepare(
      `SELECT c.id, c.body, c.created_at, c.player_id, p.display_label
       FROM game_chat c LEFT JOIN game_players p ON p.id = c.player_id
       WHERE c.room_id = ? ORDER BY c.created_at DESC LIMIT 40`
    )
    .all(row.id);
  return rows.reverse();
}

export async function postReaction(code: string, playerId: string, emoji: string) {
  const row = await loadRoomRow(code);
  if (!row) throw new Error("Room not found");
  const allowed = ["😂", "🔥", "👀", "😱", "👏", "🤔", "💀", "❤️"];
  if (!allowed.includes(emoji)) throw new Error("Bad reaction");
  const id = crypto.randomUUID();
  const db = await getDb();
  await db
    .prepare(
      `INSERT INTO game_reactions (id, room_id, player_id, emoji, created_at) VALUES (?, ?, ?, ?, ?)`
    )
    .run(id, row.id, playerId, emoji, nowIso());
  return { id, emoji };
}

export async function recentReactions(code: string) {
  const row = await loadRoomRow(code);
  if (!row) return [];
  const db = await getDb();
  return db
    .prepare(
      `SELECT emoji, player_id, created_at FROM game_reactions
       WHERE room_id = ? ORDER BY created_at DESC LIMIT 12`
    )
    .all(row.id);
}

export async function tickRoom(code: string, viewerPlayerId?: string | null) {
  await advanceIfTimedOut(code);
  await maybeAfterReveal(code);
  await runBotTurns(code);
  return getRoomPublic(code, viewerPlayerId);
}

export { FREE_BOT_LIMIT, PREMIUM_BOT_LIMIT };
