import crypto from "crypto";
import { getDb } from "@/lib/db";
import {
  DUO_QUESTIONS,
  MAP_QUESTIONS,
  THINK_QUESTIONS,
  isViralKind,
  shortCode,
  type ViralKind,
} from "./catalog";

export type ViralSpaceRow = {
  id: string;
  code: string;
  kind: string;
  owner_id: string | null;
  title: string;
  config_json: string;
  unlocked: number;
  created_at: string;
};

export type ViralAnswerRow = {
  id: string;
  space_id: string;
  side: string;
  payload_json: string;
  created_at: string;
};

function defaultConfig(kind: ViralKind, extra: Record<string, unknown> = {}) {
  if (kind === "think") return { questions: THINK_QUESTIONS, ...extra };
  if (kind === "map") return { questions: MAP_QUESTIONS, answers: extra.answers || null, ...extra };
  if (kind === "duo") return { questions: DUO_QUESTIONS, relation: extra.relation || "friends", ...extra };
  if (kind === "say") return { intent: extra.intent || "miss", message: extra.message || "", format: extra.format || "text", ...extra };
  if (kind === "when") return { trigger: extra.trigger || "need_it", message: extra.message || "", ...extra };
  if (kind === "words") return { prompt: "Describe me in three words.", ...extra };
  if (kind === "ask") return { prompt: "You get one question for me.", ...extra };
  if (kind === "fragment") return { prompt: "Leave one thing today.", ...extra };
  if (kind === "guess") return { attempts: 3, hints: extra.hints || [], ...extra };
  return extra;
}

export async function createViralSpace(input: {
  kind: ViralKind;
  ownerId: string | null;
  title: string;
  config?: Record<string, unknown>;
}): Promise<ViralSpaceRow> {
  if (!isViralKind(input.kind)) throw new Error("Unknown kind");
  const db = await getDb();
  const id = crypto.randomUUID();
  const code = shortCode();
  const now = new Date().toISOString();
  const config = defaultConfig(input.kind, input.config || {});
  await db
    .prepare(
      `INSERT INTO viral_spaces (id, code, kind, owner_id, title, config_json, unlocked, created_at)
       VALUES (?, ?, ?, ?, ?, ?, 0, ?)`
    )
    .run(id, code, input.kind, input.ownerId, input.title, JSON.stringify(config), now);
  return {
    id,
    code,
    kind: input.kind,
    owner_id: input.ownerId,
    title: input.title,
    config_json: JSON.stringify(config),
    unlocked: 0,
    created_at: now,
  };
}

export async function getSpaceByCode(code: string): Promise<ViralSpaceRow | null> {
  const db = await getDb();
  return ((await db
    .prepare(`SELECT * FROM viral_spaces WHERE code = ?`)
    .get(code.toLowerCase())) as ViralSpaceRow | undefined) || null;
}

export async function addViralAnswer(input: {
  spaceId: string;
  side?: string;
  payload: Record<string, unknown>;
}): Promise<ViralAnswerRow> {
  const db = await getDb();
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const row: ViralAnswerRow = {
    id,
    space_id: input.spaceId,
    side: input.side || "guest",
    payload_json: JSON.stringify(input.payload),
    created_at: now,
  };
  await db
    .prepare(
      `INSERT INTO viral_answers (id, space_id, side, payload_json, created_at) VALUES (?, ?, ?, ?, ?)`
    )
    .run(row.id, row.space_id, row.side, row.payload_json, row.created_at);
  return row;
}

export async function listAnswers(spaceId: string): Promise<ViralAnswerRow[]> {
  const db = await getDb();
  return (await db
    .prepare(`SELECT * FROM viral_answers WHERE space_id = ? ORDER BY created_at ASC`)
    .all(spaceId)) as ViralAnswerRow[];
}

export async function markUnlocked(spaceId: string) {
  const db = await getDb();
  await db.prepare(`UPDATE viral_spaces SET unlocked = 1 WHERE id = ?`).run(spaceId);
}

export function parseConfig(space: ViralSpaceRow): Record<string, unknown> {
  try {
    return JSON.parse(space.config_json || "{}") as Record<string, unknown>;
  } catch {
    return {};
  }
}

/** Aggregate three-word / think answers into simple frequency map. */
export function perceptionPatterns(answers: ViralAnswerRow[]): Array<{ label: string; pct: number; count: number }> {
  const counts = new Map<string, number>();
  let total = 0;
  for (const a of answers) {
    let payload: Record<string, unknown> = {};
    try {
      payload = JSON.parse(a.payload_json) as Record<string, unknown>;
    } catch {
      continue;
    }
    const words = Array.isArray(payload.words)
      ? (payload.words as unknown[]).map((w) => String(w).toLowerCase().trim()).filter(Boolean)
      : [];
    const free = typeof payload.text === "string" ? payload.text : "";
    const tokens = [
      ...words,
      ...free
        .split(/[,;\n]/)
        .map((s) => s.trim().toLowerCase())
        .filter((s) => s.length > 1 && s.length < 40),
    ];
    for (const t of tokens) {
      counts.set(t, (counts.get(t) || 0) + 1);
      total += 1;
    }
  }
  if (!total) return [];
  return [...counts.entries()]
    .map(([label, count]) => ({
      label,
      count,
      pct: Math.round((count / Math.max(answers.length, 1)) * 100),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 12);
}

export function duoScore(ownerAnswers: string[], guestAnswers: string[]): number {
  if (!ownerAnswers.length || !guestAnswers.length) return 0;
  let hit = 0;
  const n = Math.min(ownerAnswers.length, guestAnswers.length);
  for (let i = 0; i < n; i++) {
    if (
      ownerAnswers[i]?.trim().toLowerCase() &&
      ownerAnswers[i].trim().toLowerCase() === guestAnswers[i]?.trim().toLowerCase()
    ) {
      hit += 1;
    }
  }
  return Math.round((hit / n) * 100);
}

export function mapMatchScore(owner: string[], guess: string[]): number {
  return duoScore(owner, guess);
}
