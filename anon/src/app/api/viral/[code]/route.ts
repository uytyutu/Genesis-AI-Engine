import { z } from "zod";
import { getSessionUser, sanitizeText } from "@/lib/auth";
import { err, json } from "@/lib/api";
import {
  addViralAnswer,
  duoScore,
  getSpaceByCode,
  listAnswers,
  mapMatchScore,
  parseConfig,
  perceptionPatterns,
} from "@/lib/viral/store";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ code: string }> }
) {
  const { code } = await ctx.params;
  const space = await getSpaceByCode(code);
  if (!space) return err("Not found", 404);
  const user = await getSessionUser();
  const isOwner = Boolean(user && space.owner_id && user.id === space.owner_id);
  const answers = await listAnswers(space.id);
  const config = parseConfig(space);

  const publicAnswers = isOwner || space.unlocked
    ? answers.map((a) => ({
        id: a.id,
        side: a.side,
        payload: JSON.parse(a.payload_json || "{}"),
        createdAt: a.created_at,
      }))
    : answers.map((a) => ({
        id: a.id,
        side: a.side,
        createdAt: a.created_at,
      }));

  let patterns: Array<{ label: string; pct: number; count: number }> = [];
  let score: number | null = null;

  if (isOwner || space.unlocked) {
    if (space.kind === "think" || space.kind === "words") {
      patterns = perceptionPatterns(answers);
    }
    if (space.kind === "duo" || space.kind === "map") {
      const owner = answers.find((a) => a.side === "owner");
      const guest = [...answers].reverse().find((a) => a.side === "guest");
      if (owner && guest) {
        const oa = (JSON.parse(owner.payload_json || "{}").answers || []) as string[];
        const ga = (JSON.parse(guest.payload_json || "{}").answers || []) as string[];
        score = space.kind === "map" ? mapMatchScore(oa, ga) : duoScore(oa, ga);
      }
    }
  }

  return json({
    space: {
      code: space.code,
      kind: space.kind,
      title: space.title,
      unlocked: Boolean(space.unlocked),
      isOwner,
      answerCount: answers.length,
      config,
      createdAt: space.created_at,
      sharePath: `/s/${space.code}`,
    },
    answers: publicAnswers,
    patterns,
    score,
  });
}

const answerSchema = z.object({
  side: z.string().max(24).optional(),
  text: z.string().max(2000).optional(),
  words: z.array(z.string().max(40)).max(8).optional(),
  answers: z.array(z.string().max(400)).max(20).optional(),
  question: z.string().max(400).optional(),
  format: z.string().max(32).optional(),
});

export async function POST(
  req: Request,
  ctx: { params: Promise<{ code: string }> }
) {
  const { code } = await ctx.params;
  const space = await getSpaceByCode(code);
  if (!space) return err("Not found", 404);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid JSON", 400);
  }
  const parsed = answerSchema.safeParse(body);
  if (!parsed.success) return err("Invalid answer", 400);

  const user = await getSessionUser();
  let side = parsed.data.side || "guest";
  if (user && space.owner_id === user.id && (space.kind === "duo" || space.kind === "map")) {
    side = "owner";
  }

  const payload = {
    text: parsed.data.text ? sanitizeText(parsed.data.text, 2000) : undefined,
    words: parsed.data.words?.map((w) => sanitizeText(w, 40)).filter(Boolean),
    answers: parsed.data.answers?.map((a) => sanitizeText(a, 400)),
    question: parsed.data.question ? sanitizeText(parsed.data.question, 400) : undefined,
    format: parsed.data.format,
  };

  await addViralAnswer({ spaceId: space.id, side, payload });
  return json({ ok: true }, 201);
}
