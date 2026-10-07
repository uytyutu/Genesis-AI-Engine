import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { err, json } from "@/lib/api";
import { GAME_MODES } from "@/lib/games/catalog";
import { createRoom, findOrCreateRandom5 } from "@/lib/games/engine";
import { checkRateLimit } from "@/lib/rate-limit";
import { track } from "@/lib/analytics";

const schema = z.object({
  modeId: z.string(),
  displayLabel: z.string().min(1).max(40).optional(),
  randomMatch: z.boolean().optional(),
});

export async function GET() {
  return json({
    modes: GAME_MODES,
  });
}

export async function POST(req: Request) {
  const user = await getSessionUser();
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  const rl = await checkRateLimit(`room_create:${user?.id || ip}`, 20, 60 * 60 * 1000);
  if (!rl.ok) return err("Too many rooms.", 429);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) return err("Invalid room", 400);

  const label =
    sanitizeText(parsed.data.displayLabel || user?.display_name || "Player", 40) ||
    "Player";

  try {
    if (parsed.data.randomMatch || parsed.data.modeId === "random_5") {
      const room = await findOrCreateRandom5(label, user?.id);
      await track("game_random5", { code: room?.code });
      return json({ room }, 201);
    }
    const room = await createRoom({
      modeId: parsed.data.modeId as import("@/lib/games/catalog").GameModeId,
      hostId: user?.id,
      hostLabel: label,
    });
    await track("game_room_created", { modeId: parsed.data.modeId, code: room?.code });
    return json({ room }, 201);
  } catch (e) {
    return err(e instanceof Error ? e.message : "Create failed", 400);
  }
}
