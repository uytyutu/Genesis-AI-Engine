import { err, json } from "@/lib/api";
import { getPublicProfile } from "@/lib/profile";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ username: string }> }
) {
  const { username } = await ctx.params;
  const profile = await getPublicProfile(username);
  if (!profile) return err("Profile not found", 404);
  return json({
    profile,
    sharePath: `/@${profile.username}`,
  });
}
