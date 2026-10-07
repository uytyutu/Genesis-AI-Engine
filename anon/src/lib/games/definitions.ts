import type { GameModeId } from "./catalog";

export type GamePhase =
  | "lobby"
  | "ready"
  | "intro"
  | "role_reveal"
  | "question"
  | "answer"
  | "action"
  | "vote"
  | "reveal"
  | "score"
  | "final"
  | "result";

export type ChaosLevel = 1 | 2 | 3 | 4 | 5;

export interface GameDefinitionMeta {
  id: GameModeId;
  categoryKey: string;
  chaos: ChaosLevel;
  art: "mystery" | "roles" | "crowd" | "grid" | "liar" | "speed" | "caption" | "voice" | "match";
  phases: GamePhase[];
  roundSeconds: number;
  maxRounds: number;
  /** i18n keys for localized prompts (resolved at runtime by locale on client display; server stores keys) */
  promptKeys: string[];
}

export const GAME_META: Record<GameModeId, GameDefinitionMeta> = {
  who_did_it: {
    id: "who_did_it",
    categoryKey: "cat.mystery",
    chaos: 3,
    art: "mystery",
    phases: ["lobby", "intro", "question", "vote", "reveal", "score", "result"],
    roundSeconds: 20,
    maxRounds: 3,
    promptKeys: [
      "prompt.who.birthday",
      "prompt.who.late",
      "prompt.who.laugh",
    ],
  },
  secret_roles: {
    id: "secret_roles",
    categoryKey: "cat.secret",
    chaos: 4,
    art: "roles",
    phases: ["lobby", "role_reveal", "question", "vote", "reveal", "score", "result"],
    roundSeconds: 25,
    maxRounds: 2,
    promptKeys: ["prompt.roles.trust", "prompt.roles.suspect"],
  },
  battle_5x5: {
    id: "battle_5x5",
    categoryKey: "cat.teams",
    chaos: 4,
    art: "grid",
    phases: ["lobby", "intro", "action", "reveal", "score", "result"],
    roundSeconds: 18,
    maxRounds: 5,
    promptKeys: ["prompt.grid.pick"],
  },
  majority: {
    id: "majority",
    categoryKey: "cat.crowd",
    chaos: 2,
    art: "crowd",
    phases: ["lobby", "question", "reveal", "score", "result"],
    roundSeconds: 15,
    maxRounds: 4,
    promptKeys: [
      "prompt.maj.dinner",
      "prompt.maj.vacation",
      "prompt.maj.night",
      "prompt.maj.drink",
    ],
  },
  find_the_liar: {
    id: "find_the_liar",
    categoryKey: "cat.secret",
    chaos: 4,
    art: "liar",
    phases: ["lobby", "intro", "answer", "vote", "reveal", "score", "result"],
    roundSeconds: 30,
    maxRounds: 1,
    promptKeys: ["prompt.liar.story"],
  },
  secret_mission: {
    id: "secret_mission",
    categoryKey: "cat.secret",
    chaos: 3,
    art: "roles",
    phases: ["lobby", "result"],
    roundSeconds: 20,
    maxRounds: 1,
    promptKeys: [],
  },
  hidden_clues: {
    id: "hidden_clues",
    categoryKey: "cat.coop",
    chaos: 2,
    art: "mystery",
    phases: ["lobby", "result"],
    roundSeconds: 20,
    maxRounds: 1,
    promptKeys: [],
  },
  speed: {
    id: "speed",
    categoryKey: "cat.fast",
    chaos: 5,
    art: "speed",
    phases: ["lobby", "question", "reveal", "score", "result"],
    roundSeconds: 12,
    maxRounds: 3,
    promptKeys: ["prompt.speed.island", "prompt.speed.emoji", "prompt.speed.word"],
  },
  caption_war: {
    id: "caption_war",
    categoryKey: "cat.funny",
    chaos: 3,
    art: "caption",
    phases: ["lobby", "answer", "vote", "reveal", "score", "result"],
    roundSeconds: 25,
    maxRounds: 1,
    promptKeys: ["prompt.caption.five", "prompt.caption.chat", "prompt.caption.twist"],
  },
  random_5: {
    id: "random_5",
    categoryKey: "cat.strangers",
    chaos: 3,
    art: "match",
    phases: ["lobby", "question", "reveal", "score", "result"],
    roundSeconds: 15,
    maxRounds: 3,
    promptKeys: [
      "prompt.maj.dinner",
      "prompt.maj.vacation",
      "prompt.maj.night",
    ],
  },
};

export const MAJORITY_OPTIONS: Record<string, [string, string]> = {
  "prompt.maj.dinner": ["opt.pizza", "opt.burger"],
  "prompt.maj.vacation": ["opt.sea", "opt.mountains"],
  "prompt.maj.night": ["opt.cinema", "opt.home"],
  "prompt.maj.drink": ["opt.coffee", "opt.tea"],
};

export function majorityOptionsFor(promptKey: string): string[] {
  return MAJORITY_OPTIONS[promptKey] || ["opt.a", "opt.b"];
}

export const ROLES = ["citizen", "liar", "detective", "wildcard"] as const;
export type RoleId = (typeof ROLES)[number];
