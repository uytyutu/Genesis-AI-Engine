import { majorityOptionsFor } from "./definitions";
import type { GameModeId } from "./catalog";
import type { GamePhase } from "./definitions";

export type BotDifficulty = "easy" | "normal" | "hard";

export type BotPersona = {
  id: string;
  /** Display name — international, not an enum */
  name: string;
  style: "careful" | "risky" | "majority" | "bluff" | "aggressive";
  styleKey: string;
};

export const BOT_PERSONAS: BotPersona[] = [
  { id: "alex", name: "Alex", style: "risky", styleKey: "bot.style.risky" },
  { id: "mia", name: "Mia", style: "majority", styleKey: "bot.style.majority" },
  { id: "leo", name: "Leo", style: "aggressive", styleKey: "bot.style.aggressive" },
  { id: "nina", name: "Nina", style: "bluff", styleKey: "bot.style.bluff" },
  { id: "sam", name: "Sam", style: "careful", styleKey: "bot.style.careful" },
  { id: "rio", name: "Rio", style: "risky", styleKey: "bot.style.risky" },
  { id: "kai", name: "Kai", style: "majority", styleKey: "bot.style.majority" },
  { id: "zoe", name: "Zoe", style: "bluff", styleKey: "bot.style.bluff" },
];

const CAPTION_KEYS = [
  "bot.caption.1",
  "bot.caption.2",
  "bot.caption.3",
  "bot.caption.4",
  "bot.caption.5",
];

const ANSWER_KEYS = [
  "bot.answer.1",
  "bot.answer.2",
  "bot.answer.3",
  "bot.answer.4",
];

function rng(seed: string): () => number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  return () => {
    h ^= h << 13;
    h ^= h >>> 17;
    h ^= h << 5;
    return (h >>> 0) / 4294967296;
  };
}

export function pickPersona(usedNames: Set<string>): BotPersona {
  const free = BOT_PERSONAS.filter((p) => !usedNames.has(p.name));
  const pool = free.length ? free : BOT_PERSONAS;
  return pool[Math.floor(Math.random() * pool.length)];
}

export function decideBotAction(input: {
  modeId: GameModeId;
  phase: GamePhase;
  botId: string;
  personaId: string;
  difficulty: BotDifficulty;
  promptKey: string;
  players: { id: string; display_label: string; score: number; is_bot?: boolean }[];
  votes: Record<string, string>;
  answers: Record<string, string>;
  round: number;
}): { type: string; payload: Record<string, unknown> } | null {
  const persona =
    BOT_PERSONAS.find((p) => p.id === input.personaId) || BOT_PERSONAS[0];
  const rand = rng(`${input.botId}:${input.round}:${input.phase}:${input.promptKey}`);
  const others = input.players.filter((p) => p.id !== input.botId);
  if (!others.length) return null;

  const skill =
    input.difficulty === "hard" ? 0.85 : input.difficulty === "normal" ? 0.55 : 0.25;

  if (
    (input.modeId === "majority" || input.modeId === "random_5") &&
    input.phase === "question"
  ) {
    const opts = majorityOptionsFor(input.promptKey);
    let choice = opts[Math.floor(rand() * opts.length)];
    if (persona.style === "majority" && rand() < skill) {
      // bias first option as "crowd favorite" simulation
      choice = opts[0];
    }
    if (persona.style === "risky" && rand() < 0.5) choice = opts[opts.length - 1];
    return { type: "pick_option", payload: { choice } };
  }

  if (
    (input.modeId === "who_did_it" ||
      input.modeId === "secret_roles" ||
      input.modeId === "battle_5x5") &&
    (input.phase === "question" || input.phase === "vote" || input.phase === "action")
  ) {
    let target = others[Math.floor(rand() * others.length)];
    if (input.difficulty === "hard" && rand() < skill) {
      // prefer humans / high score as "suspicious"
      const humans = others.filter((p) => !p.is_bot);
      const pool = humans.length ? humans : others;
      target = [...pool].sort((a, b) => b.score - a.score)[0] || target;
    }
    if (persona.style === "careful" && rand() < 0.4) {
      target = others[Math.floor(rand() * others.length)];
    }
    return { type: "vote", payload: { targetPlayerId: target.id } };
  }

  if (input.modeId === "find_the_liar" && input.phase === "answer") {
    return {
      type: "answer",
      payload: { text: ANSWER_KEYS[Math.floor(rand() * ANSWER_KEYS.length)] },
    };
  }

  if (input.modeId === "find_the_liar" && input.phase === "vote") {
    // Prefer voting for a human if bluffing persona; otherwise random
    let target = others[Math.floor(rand() * others.length)];
    if (persona.style === "bluff" && rand() < 0.6) {
      const humans = others.filter((p) => !p.is_bot);
      if (humans.length) target = humans[Math.floor(rand() * humans.length)];
    }
    if (input.difficulty === "hard" && rand() < skill * 0.5) {
      // slight random among low-score (more "suspicious" answers later)
      target = [...others].sort((a, b) => a.score - b.score)[0] || target;
    }
    return { type: "vote_liar", payload: { targetPlayerId: target.id } };
  }

  if (input.modeId === "caption_war" && input.phase === "answer") {
    return {
      type: "caption",
      payload: { text: CAPTION_KEYS[Math.floor(rand() * CAPTION_KEYS.length)] },
    };
  }

  if (input.modeId === "caption_war" && input.phase === "vote") {
    const ids = Object.keys(input.answers).filter((id) => id !== input.botId);
    if (!ids.length) return null;
    const pick = ids[Math.floor(rand() * ids.length)];
    return { type: "vote", payload: { targetPlayerId: pick } };
  }

  if (input.modeId === "speed" && input.phase === "answer") {
    return {
      type: "answer",
      payload: { text: ANSWER_KEYS[Math.floor(rand() * ANSWER_KEYS.length)] },
    };
  }

  return null;
}
