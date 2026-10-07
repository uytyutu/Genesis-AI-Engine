/** Modular social-game catalog — UI strings via i18n keys, never raw EN enums. */

export type GameModeId =
  | "who_did_it"
  | "secret_roles"
  | "battle_5x5"
  | "majority"
  | "find_the_liar"
  | "secret_mission"
  | "hidden_clues"
  | "speed"
  | "caption_war"
  | "random_5";

export type GameLane =
  | "friends"
  | "anon"
  | "battle"
  | "secret_roles"
  | "live"
  | "trending";

export interface GameModeDef {
  id: GameModeId;
  emoji: string;
  nameKey: string;
  descKey: string;
  minPlayers: number;
  maxPlayers: number;
  durationMin: number;
  lanes: GameLane[];
  playable: boolean;
  free: boolean;
  interaction:
    | "guessing"
    | "roles"
    | "team"
    | "majority"
    | "deduction"
    | "mission"
    | "coop"
    | "speed"
    | "humor"
    | "matchmaking";
}

export const GAME_MODES: GameModeDef[] = [
  {
    id: "who_did_it",
    emoji: "🕵️",
    nameKey: "game.who_did_it",
    descKey: "game.who_did_it.desc",
    minPlayers: 3,
    maxPlayers: 10,
    durationMin: 7,
    lanes: ["friends", "anon", "trending"],
    playable: true,
    free: true,
    interaction: "guessing",
  },
  {
    id: "secret_roles",
    emoji: "🎭",
    nameKey: "game.secret_roles",
    descKey: "game.secret_roles.desc",
    minPlayers: 3,
    maxPlayers: 10,
    durationMin: 10,
    lanes: ["secret_roles", "friends"],
    playable: true,
    free: true,
    interaction: "roles",
  },
  {
    id: "battle_5x5",
    emoji: "⚔️",
    nameKey: "game.battle_5x5",
    descKey: "game.battle_5x5.desc",
    minPlayers: 2,
    maxPlayers: 10,
    durationMin: 15,
    lanes: ["battle"],
    playable: true,
    free: true,
    interaction: "team",
  },
  {
    id: "majority",
    emoji: "🧠",
    nameKey: "game.majority",
    descKey: "game.majority.desc",
    minPlayers: 2,
    maxPlayers: 40,
    durationMin: 8,
    lanes: ["friends", "live", "trending"],
    playable: true,
    free: true,
    interaction: "majority",
  },
  {
    id: "find_the_liar",
    emoji: "🤥",
    nameKey: "game.find_the_liar",
    descKey: "game.find_the_liar.desc",
    minPlayers: 4,
    maxPlayers: 12,
    durationMin: 10,
    lanes: ["friends", "anon"],
    playable: true,
    free: true,
    interaction: "deduction",
  },
  {
    id: "secret_mission",
    emoji: "🎯",
    nameKey: "game.secret_mission",
    descKey: "game.secret_mission.desc",
    minPlayers: 4,
    maxPlayers: 10,
    durationMin: 12,
    lanes: ["friends", "secret_roles"],
    playable: false,
    free: true,
    interaction: "mission",
  },
  {
    id: "hidden_clues",
    emoji: "🧩",
    nameKey: "game.hidden_clues",
    descKey: "game.hidden_clues.desc",
    minPlayers: 3,
    maxPlayers: 8,
    durationMin: 15,
    lanes: ["friends"],
    playable: false,
    free: true,
    interaction: "coop",
  },
  {
    id: "speed",
    emoji: "⚡",
    nameKey: "game.speed",
    descKey: "game.speed.desc",
    minPlayers: 2,
    maxPlayers: 20,
    durationMin: 5,
    lanes: ["live", "trending"],
    playable: true,
    free: true,
    interaction: "speed",
  },
  {
    id: "caption_war",
    emoji: "😂",
    nameKey: "game.caption_war",
    descKey: "game.caption_war.desc",
    minPlayers: 3,
    maxPlayers: 30,
    durationMin: 8,
    lanes: ["friends", "anon", "trending"],
    playable: true,
    free: true,
    interaction: "humor",
  },
  {
    id: "random_5",
    emoji: "🌎",
    nameKey: "game.random_5",
    descKey: "game.random_5.desc",
    minPlayers: 5,
    maxPlayers: 5,
    durationMin: 10,
    lanes: ["live", "anon"],
    playable: true,
    free: true,
    interaction: "matchmaking",
  },
];

export const HOME_LANES: {
  id: GameLane | "rank";
  emoji: string;
  titleKey: string;
  descKey: string;
  href: string;
}[] = [
  { id: "friends", emoji: "👥", titleKey: "lane.friends", descKey: "lane.friends.desc", href: "/play?lane=friends" },
  { id: "anon", emoji: "🕵️", titleKey: "lane.anon", descKey: "lane.anon.desc", href: "/play?lane=anon" },
  { id: "battle", emoji: "⚔️", titleKey: "lane.battle", descKey: "lane.battle.desc", href: "/play?lane=battle" },
  { id: "secret_roles", emoji: "🎭", titleKey: "lane.secret", descKey: "lane.secret.desc", href: "/play?lane=secret_roles" },
  { id: "live", emoji: "🌎", titleKey: "lane.live", descKey: "lane.live.desc", href: "/play?lane=live" },
  { id: "trending", emoji: "🔥", titleKey: "lane.trending", descKey: "lane.trending.desc", href: "/play?lane=trending" },
  { id: "rank", emoji: "🏆", titleKey: "lane.rank", descKey: "lane.rank.desc", href: "/rank" },
];

export function getMode(id: string): GameModeDef | null {
  return GAME_MODES.find((m) => m.id === id) ?? null;
}
