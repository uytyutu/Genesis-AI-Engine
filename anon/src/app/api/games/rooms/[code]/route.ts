import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { err, json } from "@/lib/api";
import {
  addBot,
  applyAction,
  joinRoom,
  listChat,
  postChat,
  postReaction,
  recentReactions,
  rematch,
  removeBot,
  setReady,
  startRoom,
  tickRoom,
} from "@/lib/games/engine";
import { checkRateLimit } from "@/lib/rate-limit";
import type { BotDifficulty } from "@/lib/games/bots";

export async function GET(
  req: Request,
  ctx: { params: Promise<{ code: string }> }
) {
  const { code } = await ctx.params;
  const url = new URL(req.url);
  const playerId = url.searchParams.get("playerId");
  const room = await tickRoom(code, playerId);
  if (!room) return err("Room not found", 404);
  const chat = await listChat(code);
  const reactions = await recentReactions(code);
  return json({ room, chat, reactions });
}

const postSchema = z.object({
  action: z.enum([
    "join",
    "start",
    "play",
    "ready",
    "rematch",
    "chat",
    "react",
    "add_bot",
    "remove_bot",
  ]),
  displayLabel: z.string().max(40).optional(),
  playerId: z.string().optional(),
  type: z.string().optional(),
  payload: z.record(z.string(), z.unknown()).optional(),
  body: z.string().max(240).optional(),
  emoji: z.string().max(8).optional(),
  ready: z.boolean().optional(),
  difficulty: z.enum(["easy", "normal", "hard"]).optional(),
  botPlayerId: z.string().optional(),
});

export async function POST(
  req: Request,
  ctx: { params: Promise<{ code: string }> }
) {
  const { code } = await ctx.params;
  const user = await getSessionUser();
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`room_act:${code}:${user?.id || ip}`, 180, 60 * 60 * 1000);
  if (!rl.ok) return err("Slow down.", 429);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = postSchema.safeParse(body);
  if (!parsed.success) return err("Invalid action", 400);

  try {
    if (parsed.data.action === "join") {
      const label =
        sanitizeText(parsed.data.displayLabel || user?.display_name || "Player", 40) ||
        "Player";
      const room = await joinRoom(code, label, user?.id);
      return json({ room });
    }
    if (parsed.data.action === "start") {
      const room = await startRoom(code, user?.id);
      return json({ room });
    }
    if (parsed.data.action === "add_bot") {
      const room = await addBot(
        code,
        (parsed.data.difficulty || "normal") as BotDifficulty,
        user?.id
      );
      return json({ room });
    }
    if (parsed.data.action === "remove_bot") {
      if (!parsed.data.botPlayerId) return err("botPlayerId required", 400);
      const room = await removeBot(code, parsed.data.botPlayerId);
      return json({ room });
    }
    if (parsed.data.action === "ready") {
      if (!parsed.data.playerId) return err("playerId required", 400);
      const room = await setReady(code, parsed.data.playerId, parsed.data.ready ?? true);
      return json({ room });
    }
    if (parsed.data.action === "rematch") {
      if (!parsed.data.playerId) return err("playerId required", 400);
      const room = await rematch(code, parsed.data.playerId);
      return json({ room });
    }
    if (parsed.data.action === "chat") {
      if (!parsed.data.playerId || !parsed.data.body) {
        return err("playerId and body required", 400);
      }
      const chatRl = await checkRateLimit(`chat:${parsed.data.playerId}`, 30, 60 * 1000);
      if (!chatRl.ok) return err("Slow down chat.", 429);
      await postChat(code, parsed.data.playerId, sanitizeText(parsed.data.body, 240) || "");
      const room = await tickRoom(code, parsed.data.playerId);
      return json({ room, chat: await listChat(code) });
    }
    if (parsed.data.action === "react") {
      if (!parsed.data.playerId || !parsed.data.emoji) {
        return err("playerId and emoji required", 400);
      }
      await postReaction(code, parsed.data.playerId, parsed.data.emoji);
      return json({
        room: await tickRoom(code, parsed.data.playerId),
        reactions: await recentReactions(code),
      });
    }
    if (parsed.data.action === "play") {
      if (!parsed.data.playerId || !parsed.data.type) {
        return err("playerId and type required", 400);
      }
      const room = await applyAction(code, parsed.data.playerId, {
        type: parsed.data.type,
        payload: parsed.data.payload,
      });
      return json({ room });
    }
    return err("Unknown action", 400);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Failed";
    if (msg === "BOT_LIMIT_FREE") {
      return err("FREE_BOT_LIMIT", 402);
    }
    if (msg === "BOT_LIMIT_PREMIUM") {
      return err("PREMIUM_BOT_LIMIT", 400);
    }
    if (msg === "HARD_BOTS_LOCKED") {
      return err("HARD_BOTS_LOCKED", 402);
    }
    return err(msg, 400);
  }
}
